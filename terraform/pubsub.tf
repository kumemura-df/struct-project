resource "google_pubsub_topic" "upload_events" {
  name = "upload-events"
}

resource "google_pubsub_subscription" "upload_events_sub" {
  name  = "upload-events-sub"
  topic = google_pubsub_topic.upload_events.name

  # Push to Worker Cloud Run service
  push_config {
    push_endpoint = google_cloud_run_service.worker.status[0].url
    
    oidc_token {
      service_account_email = google_service_account.pubsub_invoker.email
    }
    
    attributes = {
      x-goog-version = "v1"
    }
  }

  ack_deadline_seconds = 600
  message_retention_duration = "604800s" # 7 days
  
  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }
  
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.dead_letter.id
    max_delivery_attempts = 5
  }

  depends_on = [
    google_cloud_run_service.worker,
    google_cloud_run_service_iam_member.worker_pubsub_invoker,
  ]
}

# Dead letter topic for failed messages
resource "google_pubsub_topic" "dead_letter" {
  name = "upload-events-dead-letter"
}

# Grant Pub/Sub permission to publish to dead letter topic
resource "google_pubsub_topic_iam_member" "dead_letter_publisher" {
  topic  = google_pubsub_topic.dead_letter.name
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}
