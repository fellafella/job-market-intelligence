from jobmarket.extract import API_URL, extract, fetch_jobs, load_sample, validate_jobs


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(self.payload)


def test_sample_contract_accepts_valid_and_rejects_invalid():
    valid, rejected = validate_jobs(load_sample())
    assert len(valid) == 10
    assert rejected == 1  # l'offre 1011 est volontairement invalide


def test_validated_jobs_are_json_ready():
    valid, _ = validate_jobs(load_sample())
    first = valid[0]
    assert first["id"] == 1001
    assert isinstance(first["publication_date"], str)  # datetime -> ISO 8601


def test_validate_rejects_missing_required_fields():
    valid, rejected = validate_jobs([{"id": 1, "title": "x"}, {"title": "no id"}])
    assert valid == []
    assert rejected == 2


def test_fetch_jobs_passes_category_and_limit():
    session = FakeSession({"jobs": [{"id": 1}]})
    jobs = fetch_jobs("data", limit=5, session=session)
    url, kwargs = session.calls[0]
    assert url == API_URL
    assert kwargs["params"] == {"category": "data", "limit": 5}
    assert jobs == [{"id": 1}]


def test_extract_sample_mode_never_calls_api():
    jobs, rejected = extract(["data"], use_sample=True)
    assert len(jobs) == 10
    assert rejected == 1


def test_extract_deduplicates_across_categories(monkeypatch):
    sample = load_sample()[:2]
    monkeypatch.setattr("jobmarket.extract.fetch_jobs", lambda category, limit=None: sample)
    jobs, _ = extract(["data", "software-dev"])
    assert len(jobs) == 2
