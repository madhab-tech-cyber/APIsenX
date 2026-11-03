"""Emit wire schemas without storing runtime data: python -m analytics.schemas."""

import json

from pydantic import TypeAdapter

from analytics.decisions import RequestContext, SignedReply
from analytics.management import AlertDetail, AlertPage, InventoryPage
from analytics.models import Alert, ApplicationEvent, CollectorBatch, CollectorEvent
from analytics.normalization import RouteResult


def schemas():
    return {
        "application_event.v1": ApplicationEvent.model_json_schema(),
        "collector_event.v1.1": CollectorEvent.model_json_schema(),
        "collector_batch.v1": CollectorBatch.model_json_schema(),
        "analytics_alert.v1": Alert.model_json_schema(),
        "route_result.v1": TypeAdapter(RouteResult).json_schema(),
        "recommendation_request.v1": RequestContext.model_json_schema(),
        "signed_recommendation_reply.v1": SignedReply.model_json_schema(),
        "inventory_page.v1": InventoryPage.model_json_schema(),
        "alert_page.v1": AlertPage.model_json_schema(),
        "alert_detail.v1": AlertDetail.model_json_schema(),
    }


if __name__ == "__main__":
    print(json.dumps(schemas(), indent=2, sort_keys=True))
