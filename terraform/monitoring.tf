# Cloud Monitoring and Alerting Configuration
#
# Includes:
# - Error Reporting API enablement
# - Log-based metrics for key events
# - Alert policies for production monitoring

# Enable Error Reporting API
resource "google_project_service" "error_reporting_api" {
  service            = "clouderrorreporting.googleapis.com"
  disable_on_destroy = false
}

# Enable Cloud Monitoring API
resource "google_project_service" "monitoring_api" {
  service            = "monitoring.googleapis.com"
  disable_on_destroy = false
}

# ==============================================================================
# Log-based Metrics
# ==============================================================================

# Metric: API Error Count
resource "google_logging_metric" "api_errors" {
  name        = "project-progress/api-errors-${var.environment}"
  description = "Count of API errors (5xx responses)"
  
  filter = <<EOF
resource.type="cloud_run_revision"
resource.labels.service_name=~"project-progress-api-${var.environment}"
httpRequest.status>=500
EOF

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    labels {
      key         = "status_code"
      value_type  = "INT64"
      description = "HTTP status code"
    }
  }

  label_extractors = {
    "status_code" = "EXTRACT(httpRequest.status)"
  }
}

# Metric: Worker Processing Failures
resource "google_logging_metric" "worker_failures" {
  name        = "project-progress/worker-failures-${var.environment}"
  description = "Count of worker processing failures"
  
  filter = <<EOF
resource.type="cloud_run_revision"
resource.labels.service_name=~"project-progress-worker-${var.environment}"
textPayload=~"Error processing"
OR jsonPayload.message=~"Error processing"
EOF

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

# Metric: Meeting Processing Time
resource "google_logging_metric" "meeting_processing_time" {
  name        = "project-progress/meeting-processing-duration-${var.environment}"
  description = "Time taken to process meeting notes (distribution)"
  
  filter = <<EOF
resource.type="cloud_run_revision"
resource.labels.service_name=~"project-progress-worker-${var.environment}"
textPayload=~"Successfully processed meeting"
EOF

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "DISTRIBUTION"
    unit        = "s"
  }

  bucket_options {
    exponential_buckets {
      num_finite_buckets = 10
      growth_factor      = 2
      scale              = 1
    }
  }
}

# Metric: Authentication Failures
resource "google_logging_metric" "auth_failures" {
  name        = "project-progress/auth-failures-${var.environment}"
  description = "Count of authentication failures"
  
  filter = <<EOF
resource.type="cloud_run_revision"
resource.labels.service_name=~"project-progress-api-${var.environment}"
(textPayload=~"Not authenticated" OR httpRequest.status=401)
EOF

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
  }
}

# ==============================================================================
# Notification Channels (Email)
# ==============================================================================

# Email notification channel - requires manual verification
resource "google_monitoring_notification_channel" "email" {
  count        = var.alert_email != "" ? 1 : 0
  display_name = "Project Progress Alerts (${var.environment})"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
}

# ==============================================================================
# Alert Policies (Production only)
# ==============================================================================

# Alert: High API Error Rate
resource "google_monitoring_alert_policy" "api_error_rate" {
  count        = var.environment == "prod" ? 1 : 0
  display_name = "[${upper(var.environment)}] High API Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "API Error Rate > 5% for 5 minutes"
    
    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"project-progress-api-${var.environment}\" AND metric.type=\"run.googleapis.com/request_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      duration        = "300s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = var.alert_email != "" ? [google_monitoring_notification_channel.email[0].id] : []
  
  alert_strategy {
    auto_close = "604800s"  # 7 days
  }
  
  documentation {
    content   = <<EOF
# High API Error Rate Alert

The API service is experiencing a high rate of 5xx errors.

## Investigation Steps:
1. Check Cloud Run logs: https://console.cloud.google.com/run/detail/${var.region}/project-progress-api-${var.environment}/logs
2. Check Error Reporting: https://console.cloud.google.com/errors
3. Verify BigQuery connectivity
4. Check OAuth/JWT configuration

## Potential Causes:
- Database connection issues
- Memory/CPU exhaustion
- External service failures (Vertex AI, BigQuery)
EOF
    mime_type = "text/markdown"
  }
  
  depends_on = [google_project_service.monitoring_api]
}

# Alert: Worker Processing Failures
resource "google_monitoring_alert_policy" "worker_failures" {
  count        = var.environment == "prod" ? 1 : 0
  display_name = "[${upper(var.environment)}] Worker Processing Failures"
  combiner     = "OR"
  
  conditions {
    display_name = "Worker failures > 3 in 10 minutes"
    
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/project-progress/worker-failures-${var.environment}\""
      comparison      = "COMPARISON_GT"
      threshold_value = 3
      duration        = "600s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_SUM"
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = var.alert_email != "" ? [google_monitoring_notification_channel.email[0].id] : []
  
  alert_strategy {
    auto_close = "604800s"
  }
  
  documentation {
    content   = <<EOF
# Worker Processing Failures Alert

The worker service is failing to process meeting notes.

## Investigation Steps:
1. Check Worker logs: https://console.cloud.google.com/run/detail/${var.region}/project-progress-worker-${var.environment}/logs
2. Check Pub/Sub dead-letter queue
3. Verify Vertex AI API status
4. Check meeting status in BigQuery (ERROR status)

## Potential Causes:
- Vertex AI quota exhaustion
- Invalid input file format
- BigQuery write failures
EOF
    mime_type = "text/markdown"
  }
  
  depends_on = [
    google_project_service.monitoring_api,
    google_logging_metric.worker_failures,
  ]
}

# Alert: Service Unavailability (Uptime Check)
resource "google_monitoring_uptime_check_config" "api_health" {
  count        = var.environment == "prod" ? 1 : 0
  display_name = "API Health Check (${var.environment})"
  timeout      = "10s"
  period       = "60s"
  
  http_check {
    path         = "/"
    port         = 443
    use_ssl      = true
    validate_ssl = true
  }
  
  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(google_cloud_run_service.api.status[0].url, "https://", "")
    }
  }
  
  depends_on = [google_project_service.monitoring_api]
}

# Alert: API Downtime
resource "google_monitoring_alert_policy" "api_downtime" {
  count        = var.environment == "prod" ? 1 : 0
  display_name = "[${upper(var.environment)}] API Service Down"
  combiner     = "OR"
  
  conditions {
    display_name = "API uptime check failing"
    
    condition_threshold {
      filter          = "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND resource.type=\"uptime_url\" AND metric.labels.check_id=\"${google_monitoring_uptime_check_config.api_health[0].uptime_check_id}\""
      comparison      = "COMPARISON_LT"
      threshold_value = 1
      duration        = "300s"
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_FRACTION_TRUE"
      }
      
      trigger {
        count = 1
      }
    }
  }
  
  notification_channels = var.alert_email != "" ? [google_monitoring_notification_channel.email[0].id] : []
  
  alert_strategy {
    auto_close = "604800s"
  }
  
  documentation {
    content   = <<EOF
# API Service Down Alert

The API service health check is failing.

## Immediate Actions:
1. Check Cloud Run status: https://console.cloud.google.com/run/detail/${var.region}/project-progress-api-${var.environment}
2. Check for recent deployments
3. Verify service account permissions
4. Check for quota exhaustion

## Escalation:
Contact the on-call engineer if the issue persists for more than 15 minutes.
EOF
    mime_type = "text/markdown"
  }
  
  depends_on = [
    google_project_service.monitoring_api,
    google_monitoring_uptime_check_config.api_health,
  ]
}

# ==============================================================================
# Dashboard
# ==============================================================================

resource "google_monitoring_dashboard" "main" {
  count          = var.environment == "prod" ? 1 : 0
  dashboard_json = <<EOF
{
  "displayName": "Project Progress DB - ${upper(var.environment)}",
  "gridLayout": {
    "columns": 2,
    "widgets": [
      {
        "title": "API Request Count",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"project-progress-api-${var.environment}\" AND metric.type=\"run.googleapis.com/request_count\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_RATE"
                }
              }
            }
          }]
        }
      },
      {
        "title": "API Latency (p99)",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"project-progress-api-${var.environment}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_PERCENTILE_99"
                }
              }
            }
          }]
        }
      },
      {
        "title": "Worker Processing",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"project-progress-worker-${var.environment}\" AND metric.type=\"run.googleapis.com/request_count\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_RATE"
                }
              }
            }
          }]
        }
      },
      {
        "title": "Error Rate",
        "xyChart": {
          "dataSets": [{
            "timeSeriesQuery": {
              "timeSeriesFilter": {
                "filter": "metric.type=\"logging.googleapis.com/user/project-progress/api-errors-${var.environment}\"",
                "aggregation": {
                  "alignmentPeriod": "60s",
                  "perSeriesAligner": "ALIGN_SUM"
                }
              }
            }
          }]
        }
      }
    ]
  }
}
EOF

  depends_on = [google_project_service.monitoring_api]
}

# ==============================================================================
# Variables
# ==============================================================================

variable "alert_email" {
  description = "Email address for alert notifications (optional)"
  type        = string
  default     = ""
}

# ==============================================================================
# Outputs
# ==============================================================================

output "monitoring_dashboard_url" {
  value       = var.environment == "prod" ? "https://console.cloud.google.com/monitoring/dashboards/builder/${google_monitoring_dashboard.main[0].id}?project=${var.project_id}" : null
  description = "URL to the Cloud Monitoring dashboard"
}

output "error_reporting_url" {
  value       = "https://console.cloud.google.com/errors?project=${var.project_id}"
  description = "URL to Error Reporting console"
}

