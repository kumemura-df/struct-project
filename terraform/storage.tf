resource "google_storage_bucket" "meeting_notes_raw" {
  name          = "${var.project_id}-meeting-notes-raw"
  location      = var.location
  force_destroy = true

  uniform_bucket_level_access = true
}
