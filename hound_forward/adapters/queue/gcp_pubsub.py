from __future__ import annotations

import base64
import json
from typing import Any

from hound_forward.ports import Job, deserialize_job, serialize_job


class PubSubJobQueue:
    """Publish jobs to Pub/Sub topics and optionally pull them from subscriptions."""

    def __init__(
        self,
        *,
        project_id: str,
        topic: str,
        subscription: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        if not project_id:
            raise ValueError("PubSubJobQueue requires a project_id.")
        if not topic:
            raise ValueError("PubSubJobQueue requires a topic.")
        self.project_id = project_id
        self.topic = topic
        self.subscription = subscription
        self.endpoint = endpoint
        self._publisher = None
        self._subscriber = None

    def enqueue(self, job: Job) -> None:
        publisher = self._get_publisher()
        topic_path = self._publisher.topic_path(self.project_id, self.topic)
        payload = json.dumps(serialize_job(job)).encode("utf-8")
        publisher.publish(topic_path, payload).result()

    def dequeue(self) -> Job | None:
        if not self.subscription:
            raise ValueError("PubSubJobQueue requires a subscription for dequeue operations.")
        subscriber = self._get_subscriber()
        subscription_path = subscriber.subscription_path(self.project_id, self.subscription)
        response = subscriber.pull(subscription=subscription_path, max_messages=1)
        if not response.received_messages:
            return None
        received = response.received_messages[0]
        payload = json.loads(received.message.data.decode("utf-8"))
        subscriber.acknowledge(subscription=subscription_path, ack_ids=[received.ack_id])
        return deserialize_job(payload)

    @staticmethod
    def decode_push_envelope(envelope: dict[str, Any]) -> Job:
        message = envelope.get("message", {})
        encoded = message.get("data")
        if not encoded:
            raise ValueError("Pub/Sub push request did not include a message.data payload.")
        decoded = base64.b64decode(encoded)
        payload = json.loads(decoded.decode("utf-8"))
        return deserialize_job(payload)

    @staticmethod
    def _build_clients(*, endpoint: str | None):
        from google.cloud import pubsub_v1

        publisher_options = {"api_endpoint": endpoint} if endpoint else None
        subscriber_options = {"api_endpoint": endpoint} if endpoint else None
        return (
            pubsub_v1.PublisherClient(client_options=publisher_options),
            pubsub_v1.SubscriberClient(client_options=subscriber_options),
        )

    def _get_publisher(self):
        if self._publisher is None:
            self._publisher, self._subscriber = self._build_clients(endpoint=self.endpoint)
        return self._publisher

    def _get_subscriber(self):
        if self._subscriber is None:
            self._publisher, self._subscriber = self._build_clients(endpoint=self.endpoint)
        return self._subscriber
