from unittest.mock import Mock
from uuid import UUID

from fastapi.testclient import TestClient

import app.main as main_module


client = TestClient(main_module.app)
client_without_server_exceptions = TestClient(
    main_module.app,
    raise_server_exceptions=False,
)

TEST_API_KEY = "test-api-key"
API_HEADERS = {"X-API-Key": TEST_API_KEY}


VALID_PAYLOAD = {
    "PrimaryPropertyType": "Hotel",
    "Neighborhood": "DOWNTOWN",
    "LargestPropertyUseType": "Hotel",
    "SecondLargestPropertyUseType": "None",
    "ThirdLargestPropertyUseType": "None",
    "YearBuilt_decade_cat": "1920s",
    "YearBuilt": 1927,
    "NumberofBuildings": 1.0,
    "NumberofFloors": 12.0,
    "PropertyGFATotal": 88434.0,
    "PropertyGFAParking": 0.0,
    "est_multi_usage": 0,
    "has_SecondLargestPropertyUseType": 0,
    "share_gfa_main": 1.0,
    "has_geo": 1,
    "log_geo_cell_150m_count": 0.6931471805599453,
    "has_gas": 1,
}


PREDICTION_RESULT = {
    "predicted_site_energy_use_kbtu": 1313220.69,
    "predicted_site_energy_use_gwh": 0.3849,
    "audit_priority": "priorité normale",
    "model_type": "RandomForestRegressor",
    "model_version": "local-v0.1.0",
}


def test_predict_without_database_logging(monkeypatch):
    """
    When logging is disabled, the API predicts without calling PostgreSQL.
    """
    predict_mock = Mock(return_value=PREDICTION_RESULT)
    create_request_mock = Mock()

    monkeypatch.setattr(
        main_module,
        "DATABASE_LOGGING_ENABLED",
        False,
    )
    monkeypatch.setattr(
        main_module,
        "predict_energy",
        predict_mock,
    )
    monkeypatch.setattr(
        main_module,
        "create_prediction_request",
        create_request_mock,
    )

    response = client.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == PREDICTION_RESULT

    predict_mock.assert_called_once()
    create_request_mock.assert_not_called()


def test_predict_with_successful_database_logging(monkeypatch):
    """
    When logging is enabled, the request and result are both recorded.
    """
    request_id = UUID("11111111-1111-1111-1111-111111111111")

    create_request_mock = Mock(return_value=request_id)
    predict_mock = Mock(return_value=PREDICTION_RESULT)
    save_result_mock = Mock()
    mark_error_mock = Mock()

    monkeypatch.setattr(
        main_module,
        "DATABASE_LOGGING_ENABLED",
        True,
    )
    monkeypatch.setattr(
        main_module,
        "create_prediction_request",
        create_request_mock,
    )
    monkeypatch.setattr(
        main_module,
        "predict_energy",
        predict_mock,
    )
    monkeypatch.setattr(
        main_module,
        "save_prediction_result",
        save_result_mock,
    )
    monkeypatch.setattr(
        main_module,
        "mark_prediction_request_as_error",
        mark_error_mock,
    )

    response = client.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers=API_HEADERS,
    )

    assert response.status_code == 200
    assert response.json() == PREDICTION_RESULT

    create_request_mock.assert_called_once_with(
        input_data=VALID_PAYLOAD,
        source="api",
    )
    save_result_mock.assert_called_once_with(
        request_id=request_id,
        model_version="local-v0.1.0",
        prediction=PREDICTION_RESULT,
    )
    mark_error_mock.assert_not_called()


def test_predict_marks_request_as_error_when_prediction_fails(
    monkeypatch,
):
    """
    When prediction fails, the existing request is marked as an error.
    """
    request_id = UUID("22222222-2222-2222-2222-222222222222")

    create_request_mock = Mock(return_value=request_id)
    predict_mock = Mock(
        side_effect=RuntimeError("Simulated prediction failure")
    )
    save_result_mock = Mock()
    mark_error_mock = Mock()

    monkeypatch.setattr(
        main_module,
        "DATABASE_LOGGING_ENABLED",
        True,
    )
    monkeypatch.setattr(
        main_module,
        "create_prediction_request",
        create_request_mock,
    )
    monkeypatch.setattr(
        main_module,
        "predict_energy",
        predict_mock,
    )
    monkeypatch.setattr(
        main_module,
        "save_prediction_result",
        save_result_mock,
    )
    monkeypatch.setattr(
        main_module,
        "mark_prediction_request_as_error",
        mark_error_mock,
    )

    response = client_without_server_exceptions.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers=API_HEADERS,
    )

    assert response.status_code == 500

    mark_error_mock.assert_called_once_with(
        request_id=request_id,
        error_message="Simulated prediction failure",
    )
    save_result_mock.assert_not_called()
