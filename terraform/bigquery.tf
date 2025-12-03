resource "google_bigquery_dataset" "main" {
  dataset_id    = var.bigquery_dataset
  friendly_name = "Project Progress DB (${var.environment})"
  description   = "Dataset for Project Progress DB - ${var.environment} environment"
  location      = var.location
  
  labels = {
    environment = var.environment
  }
}

resource "google_bigquery_table" "meetings" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "meetings"
  schema     = <<EOF
[
  {
    "name": "meeting_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "tenant_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "meeting_date",
    "type": "DATE",
    "mode": "NULLABLE"
  },
  {
    "name": "title",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "source_file_uri",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "language",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "status",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "error_message",
    "type": "STRING",
    "mode": "NULLABLE"
  }
]
EOF
}

resource "google_bigquery_table" "projects" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "projects"
  schema     = <<EOF
[
  {
    "name": "project_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "tenant_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "project_name",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "latest_meeting_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "updated_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  }
]
EOF
}

resource "google_bigquery_table" "tasks" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "tasks"
  schema     = <<EOF
[
  {
    "name": "task_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "tenant_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "meeting_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "project_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "task_title",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "task_description",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "owner",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "owner_email",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "due_date",
    "type": "DATE",
    "mode": "NULLABLE"
  },
  {
    "name": "status",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "priority",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "updated_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "source_sentence",
    "type": "STRING",
    "mode": "NULLABLE"
  }
]
EOF
}

resource "google_bigquery_table" "risks" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "risks"
  schema     = <<EOF
[
  {
    "name": "risk_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "tenant_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "meeting_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "project_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "risk_description",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "risk_level",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "likelihood",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "impact",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "owner",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "source_sentence",
    "type": "STRING",
    "mode": "NULLABLE"
  }
]
EOF
}

resource "google_bigquery_table" "decisions" {
  dataset_id = google_bigquery_dataset.main.dataset_id
  table_id   = "decisions"
  schema     = <<EOF
[
  {
    "name": "decision_id",
    "type": "STRING",
    "mode": "REQUIRED"
  },
  {
    "name": "tenant_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "meeting_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "project_id",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "decision_content",
    "type": "STRING",
    "mode": "NULLABLE"
  },
  {
    "name": "created_at",
    "type": "TIMESTAMP",
    "mode": "NULLABLE"
  },
  {
    "name": "source_sentence",
    "type": "STRING",
    "mode": "NULLABLE"
  }
]
EOF
}
