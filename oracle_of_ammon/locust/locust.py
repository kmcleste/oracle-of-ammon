from locust import HttpUser, between, task


# TODO: Dynamically set tasks based on config file
class Tests(HttpUser):
    wait_time = between(2, 4)

    @task
    def health(self):
        self.client.get(url="/health")

    @task
    def root(self):
        self.client.get(url="/")
