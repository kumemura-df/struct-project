from google.cloud import bigquery
from typing import List, Dict, Any
import os
import uuid
from datetime import datetime

class BigQueryClient:
    def __init__(self):
        self.client = bigquery.Client()
        self.dataset_id = "project_progress_db"

    def insert_meeting(self, meeting_data: Dict[str, Any]) -> str:
        table_id = f"{self.client.project}.{self.dataset_id}.meetings"
        errors = self.client.insert_rows_json(table_id, [meeting_data])
        if errors:
            raise Exception(f"BigQuery insert error: {errors}")
        return meeting_data["meeting_id"]

    def insert_tasks(self, tasks: List[Dict[str, Any]]):
        if not tasks:
            return
        table_id = f"{self.client.project}.{self.dataset_id}.tasks"
        errors = self.client.insert_rows_json(table_id, tasks)
        if errors:
            raise Exception(f"BigQuery insert error: {errors}")

    def insert_risks(self, risks: List[Dict[str, Any]]):
        if not risks:
            return
        table_id = f"{self.client.project}.{self.dataset_id}.risks"
        errors = self.client.insert_rows_json(table_id, risks)
        if errors:
            raise Exception(f"BigQuery insert error: {errors}")

    def insert_decisions(self, decisions: List[Dict[str, Any]]):
        if not decisions:
            return
        table_id = f"{self.client.project}.{self.dataset_id}.decisions"
        errors = self.client.insert_rows_json(table_id, decisions)
        if errors:
            raise Exception(f"BigQuery insert error: {errors}")

    def insert_projects(self, projects: List[Dict[str, Any]]):
        if not projects:
            return
        # For projects, we might want to use MERGE to avoid duplicates, 
        # but for MVP simple insert or ignore is fine. 
        # Here we just insert, assuming upstream handles dedup or we accept duplicates for now.
        table_id = f"{self.client.project}.{self.dataset_id}.projects"
        errors = self.client.insert_rows_json(table_id, projects)
        if errors:
            # Ignore errors for now as projects might already exist
            print(f"BigQuery insert projects warning: {errors}")

    def get_projects(self) -> List[Dict[str, Any]]:
        query = f"""
            SELECT * FROM `{self.dataset_id}.projects`
        """
        query_job = self.client.query(query)
        return [dict(row) for row in query_job]

    def get_tasks(self, project_id: str = None) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM `{self.dataset_id}.tasks`"
        if project_id:
            query += f" WHERE project_id = '{project_id}'"
        query_job = self.client.query(query)
        return [dict(row) for row in query_job]
