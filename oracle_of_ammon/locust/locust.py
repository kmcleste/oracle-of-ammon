from locust import HttpUser, task, between


class Tests(HttpUser):
    wait_time = between(2, 4)

    @task
    def search(self):
        self.client.post(
            url="/search",
            json={
                "query": "This is a question",
                "params": {"Retriever": {"top_k": 10}},
            },
        )

    @task
    def health(self):
        self.client.get(url="/health")

    @task
    def get_documents(self):
        self.client.get(url="/get-documents")

    @task
    def summary(self):
        self.client.get(url="/summary")
