import time

import environ
import urllib3
from django.core.management.base import BaseCommand, CommandParser
from elasticsearch import Elasticsearch

from scoap3.tasks import upload_index_range

env = environ.Env()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class Command(BaseCommand):
    help = "Import records from elasticsearch index."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--host",
            type=str,
            required=True,
            help="URL of the elastic search instance.",
        )
        parser.add_argument(
            "--port",
            type=int,
            required=True,
            help="Port of the elastic search instance.",
        )
        parser.add_argument(
            "--index",
            type=str,
            required=True,
            help="Elasticsearch index to export from.",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=1000,
            required=False,
            help="Batchsize for upload per task",
        )
        parser.add_argument(
            "--username",
            type=str,
            required=False,
            help="Username for Elasticsearch. Uses OPENSEARCH_USER if empty.",
        )
        parser.add_argument(
            "--password",
            type=str,
            required=False,
            help="Password for Elasticsearch. Uses OPENSEARCH_PASSWORD if empty.",
        )

    def handle(self, *args, **options):
        if not options["username"]:
            options["username"] = env("OPENSEARCH_USER")
        if not options["password"]:
            options["password"] = env("OPENSEARCH_PASSWORD")

        timestamp = round(time.time() * 1000)
        es_settings = [
            dict(
                host=options["host"],
                port=options["port"],
                http_auth=(options["username"], options["password"]),
                use_ssl=True,
                verify_certs=False,
                timeout=60,
                url_prefix="es",
                http_compress=True,
            )
        ]

        es = Elasticsearch(es_settings)
        es.indices.refresh(options["index"])
        scroll = "30s"
        response = es.search(
            index=options["index"],
            scroll=scroll,
            size=options["batch_size"],
            body={"query": {"match_all": {}}},
        )

        scroll_id = response["_scroll_id"]
        total_docs = response["hits"]["total"]["value"]
        self.stdout.write(f"Found {total_docs} records.")
        processed = 0
        while processed < total_docs:
            documents = response["hits"]["hits"]
            doc_ids = [doc["_id"] for doc in documents]
            upload_index_range.delay(es_settings, options["index"], doc_ids, timestamp)
            processed += len(doc_ids)
            response = es.scroll(scroll_id=scroll_id, scroll=scroll)
        es.clear_scroll(scroll_id=scroll_id)
