"""RN acceptance baseline: strict contract matching, never heuristic routing."""

import hashlib
import hmac
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import unquote_to_bytes

import yaml

METHOD = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]{1,16}\Z", re.ASCII)
TRIPLET = re.compile(r"%[0-9a-fA-F]{2}")
OPERATIONS = frozenset(
    {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
)
ORDER_PATTERN = "^[A-Za-z0-9-]+$"


class ContractError(ValueError):
    def __init__(self):
        super().__init__("Unsupported or ambiguous OpenAPI contract")


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str) or key in result:
            raise ContractError()
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


@dataclass(frozen=True)
class RouteResult:
    method: str | None
    route: str | None
    classification: str
    unknown_route_token: str | None
    unknown_route_key_version: str | None
    reason_code: str
    contract_version: str

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Template:
    route: str
    segments: tuple[str, ...]
    parameters: dict
    methods: frozenset[str]

    @property
    def specificity(self):
        return len(self.parameters)


class RouteNormalizer:
    def __init__(self, content: bytes, key: bytes, key_version: str):
        if len(key) < 32 or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", key_version):
            raise ValueError("A runtime HMAC key and bounded version are required")
        self._key = key
        self.key_version = key_version
        # Normalize line endings for consistent Windows and Unix contract hashes.
        canonical_content = content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
        contract_hash = hashlib.sha256(canonical_content).hexdigest()
        self.contract_version = "sha256:" + contract_hash
        try:
            loader = UniqueLoader(canonical_content.decode("utf-8-sig"))
            try:
                contract = loader.get_single_data()
            finally:
                loader.dispose()
            if not contract["info"]["version"] or not contract["paths"]:
                raise ContractError()
            self.templates = self._compile(contract)
        except (KeyError, TypeError, ValueError, AttributeError, yaml.YAMLError):
            raise ContractError() from None

    @classmethod
    def from_file(cls, path: Path, key: bytes, key_version: str):
        return cls(path.read_bytes(), key, key_version)

    @staticmethod
    def _compile(contract):
        templates = []
        for route, item in contract["paths"].items():
            if not route.startswith("/") or any(
                x in route for x in ("?", "#", "%", "\\")
            ):
                raise ContractError()
            segments = tuple(route[1:].split("/")) if route != "/" else ()
            parameters = {}
            methods = frozenset(name.upper() for name in item if name in OPERATIONS)
            if not methods or any(not segment for segment in segments):
                raise ContractError()
            all_parameters = list(item.get("parameters", []))
            for name in item:
                if name in OPERATIONS:
                    all_parameters.extend(item[name].get("parameters", []))
            definitions = {}
            for parameter in all_parameters:
                if "$ref" in parameter:
                    prefix = "#/components/parameters/"
                    if not parameter["$ref"].startswith(prefix):
                        raise ContractError()
                    parameter = contract["components"]["parameters"][
                        parameter["$ref"][len(prefix) :]
                    ]
                if parameter.get("in") != "path":
                    continue
                schema = parameter["schema"]
                if (
                    parameter.get("required") is not True
                    or schema.get("type") != "string"
                ):
                    raise ContractError()
                if set(schema) - {"type", "minLength", "maxLength", "pattern"}:
                    raise ContractError()
                if schema.get("pattern") != ORDER_PATTERN:
                    raise ContractError()
                minimum, maximum = schema.get("minLength"), schema.get("maxLength")
                if type(minimum) is not int or type(maximum) is not int:
                    raise ContractError()
                if not 1 <= minimum <= maximum <= 128:
                    raise ContractError()
                name = parameter["name"]
                if name in definitions and definitions[name] != schema:
                    raise ContractError()
                definitions[name] = schema
            used = set()
            for index, segment in enumerate(segments):
                match = re.fullmatch(r"\{([A-Za-z][A-Za-z0-9_]*)\}", segment)
                if match:
                    name = match[1]
                    if name in used:
                        raise ContractError()
                    used.add(name)
                    parameters[index] = definitions[name]
                elif "{" in segment or "}" in segment or segment in {".", ".."}:
                    raise ContractError()
            if used != set(definitions):
                raise ContractError()
            template = Template(route, segments, parameters, methods)
            for prior in templates:
                if len(prior.segments) != len(segments):
                    continue
                overlap = all(
                    i in prior.parameters or i in parameters or left == right
                    for i, (left, right) in enumerate(
                        zip(prior.segments, segments, strict=True)
                    )
                )
                if overlap and prior.specificity == template.specificity:
                    raise ContractError()
            templates.append(template)
        return tuple(
            sorted(templates, key=lambda entry: (entry.specificity, entry.route))
        )

    def _result(self, method, route, classification, reason, path=None):
        token = None
        version = None
        if path is not None:
            token = hmac.new(
                self._key, b"unknown-route\0" + path.encode(), "sha256"
            ).hexdigest()
            version = self.key_version
        return RouteResult(
            method, route, classification, token, version, reason, self.contract_version
        )

    def normalize(self, method, target):
        if not isinstance(method, str) or not METHOD.fullmatch(method):
            return self._result(None, None, "invalid", "INVALID_METHOD")
        method = method.upper()

        def invalid(reason):
            return self._result(method, None, "invalid", reason)

        if not isinstance(target, str) or not target or len(target) > 4096:
            return invalid("INVALID_PATH_BOUNDS")
        try:
            if len(target.encode("utf-8")) > 4096:
                return invalid("INVALID_PATH_BOUNDS")
        except UnicodeError:
            return invalid("INVALID_PATH_ENCODING")
        path = target.split("?", 1)[0]
        if not path.startswith("/") or len(path.encode()) > 2048:
            return invalid("INVALID_PATH_BOUNDS")
        if "#" in target or "\\" in path or "//" in path:
            return invalid("AMBIGUOUS_PATH_SYNTAX")
        if any(ord(char) < 32 or ord(char) == 127 for char in path):
            return invalid("INVALID_PATH_ENCODING")
        if "%" in TRIPLET.sub("", path):
            return invalid("INVALID_PATH_ENCODING")
        if re.search(r"%(?:2f|5c)", path, re.I):
            return invalid("INVALID_PATH_ENCODING")
        try:
            decoded = unquote_to_bytes(path).decode("utf-8", errors="strict")
        except UnicodeError:
            return invalid("INVALID_PATH_ENCODING")
        if TRIPLET.search(decoded) or any(
            ord(c) < 32 or ord(c) == 127 for c in decoded
        ):
            return invalid("INVALID_PATH_ENCODING")
        segments = decoded[1:].split("/") if decoded != "/" else []
        if any(segment in {".", ".."} for segment in segments):
            return invalid("AMBIGUOUS_PATH_SYNTAX")
        if len(segments) > 32 or any(
            len(segment.encode()) > 128 for segment in segments
        ):
            return invalid("INVALID_PATH_BOUNDS")
        for template in self.templates:
            if len(segments) != len(template.segments):
                continue
            if not all(
                index in template.parameters or value == segments[index]
                for index, value in enumerate(template.segments)
            ):
                continue
            for index, schema in template.parameters.items():
                value = segments[index]
                # Empty trailing segment is an undocumented trailing slash, not an ID.
                if not value:
                    break
                if not schema["minLength"] <= len(value) <= schema["maxLength"]:
                    return invalid("INVALID_PARAMETER")
                if not re.fullmatch(schema["pattern"], value, flags=re.ASCII):
                    return invalid("INVALID_PARAMETER")
            else:
                if method in template.methods:
                    return self._result(
                        method, template.route, "documented", "DOCUMENTED_OPERATION"
                    )
                return self._result(
                    method,
                    template.route,
                    "method_not_documented",
                    "METHOD_NOT_IN_CONTRACT",
                )
        return self._result(
            method,
            "/__unknown__",
            "path_not_documented",
            "PATH_NOT_IN_CONTRACT",
            decoded,
        )
