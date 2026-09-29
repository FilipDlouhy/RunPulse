from django.db import connection


class HealthRepository:
    def ping(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
