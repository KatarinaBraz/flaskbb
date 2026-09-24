from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import RequestException

import flaskbb.user.services.validators as validators_module

from flaskbb.core.exceptions import StopValidation, ValidationError
from flaskbb.user.services.validators import (
    CantShareEmailValidator,
    EmailsMustBeDifferent,
    OldEmailMustMatch,
    OldPasswordMustMatch,
    PasswordsMustBeDifferent,
    ValidateAvatarURL,
)

@pytest.fixture(autouse=True)
def mock_translation(monkeypatch):
    """Keeps these unit tests independent from FlaskBB's settings database."""
    monkeypatch.setattr(
        validators_module,
        "_",
        lambda message, **kwargs: message % kwargs,
    )


@pytest.mark.parametrize(
    "current_email,old_email,should_raise",
    [
        ("katarina@email.com", "katarina@email.com", False),
        ("user@example.com", "user@example.com", False),
        ("katarina@email.com", "wrong@email.com", True),
        ("USER@example.com", "user@example.com", True),
    ],
)
def test_old_email_must_match_parametrized(
    current_email, old_email, should_raise
):
    """Checks valid and invalid combinations of the user's old email."""
    validator = OldEmailMustMatch()
    user = SimpleNamespace(email=current_email)
    changeset = SimpleNamespace(old_email=old_email)

    if should_raise:
        with pytest.raises(StopValidation):
            validator.validate(user, changeset)
    else:
        validator.validate(user, changeset)


def test_emails_must_be_different_accepts_new_email():
    validator = EmailsMustBeDifferent()
    user = SimpleNamespace(email="old@email.com")
    changeset = SimpleNamespace(new_email="new@email.com")

    validator.validate(user, changeset)


def test_emails_must_be_different_rejects_same_email():
    validator = EmailsMustBeDifferent()
    user = SimpleNamespace(email="same@email.com")
    changeset = SimpleNamespace(new_email="same@email.com")

    with pytest.raises(ValidationError):
        validator.validate(user, changeset)


def test_passwords_must_be_different_accepts_new_password():
    validator = PasswordsMustBeDifferent()
    user = Mock()
    user.check_password.return_value = False
    changeset = SimpleNamespace(new_password="a-new-password")

    validator.validate(user, changeset)

    user.check_password.assert_called_once_with("a-new-password")


def test_passwords_must_be_different_rejects_current_password():
    validator = PasswordsMustBeDifferent()
    user = Mock()
    user.check_password.return_value = True
    changeset = SimpleNamespace(new_password="current-password")

    with pytest.raises(ValidationError):
        validator.validate(user, changeset)


def test_old_password_must_match_accepts_correct_password():
    validator = OldPasswordMustMatch()
    user = Mock()
    user.check_password.return_value = True
    changeset = SimpleNamespace(old_password="correct-password")

    validator.validate(user, changeset)

    user.check_password.assert_called_once_with("correct-password")


def test_old_password_must_match_rejects_wrong_password():
    validator = OldPasswordMustMatch()
    user = Mock()
    user.check_password.return_value = False
    changeset = SimpleNamespace(old_password="wrong-password")

    with pytest.raises(StopValidation):
        validator.validate(user, changeset)


def test_avatar_validator_ignores_empty_avatar():
    validator = ValidateAvatarURL()
    changeset = SimpleNamespace(avatar="")

    with patch(
        "flaskbb.user.services.validators.check_image"
    ) as check_image_mock:
        validator.validate(Mock(), changeset)

    check_image_mock.assert_not_called()


def test_avatar_validator_calls_check_image_for_valid_url():
    validator = ValidateAvatarURL()
    avatar_url = "https://example.com/avatar.png"
    changeset = SimpleNamespace(avatar=avatar_url)

    with patch(
        "flaskbb.user.services.validators.check_image",
        return_value=(None, None),
    ) as check_image_mock:
        validator.validate(Mock(), changeset)

    check_image_mock.assert_called_once_with(avatar_url)


def test_avatar_validator_rejects_invalid_image():
    validator = ValidateAvatarURL()
    changeset = SimpleNamespace(avatar="https://example.com/not-image.txt")

    with patch(
        "flaskbb.user.services.validators.check_image",
        return_value=("Invalid image", None),
    ):
        with pytest.raises(ValidationError):
            validator.validate(Mock(), changeset)


def test_avatar_validator_handles_request_error():
    validator = ValidateAvatarURL()
    changeset = SimpleNamespace(avatar="https://example.com/avatar.png")

    with patch(
        "flaskbb.user.services.validators.check_image",
        side_effect=RequestException,
    ):
        with pytest.raises(ValidationError):
            validator.validate(Mock(), changeset)


def test_cant_share_email_accepts_unique_email():
    users = Mock()
    users.query.filter.return_value.count.return_value = 0

    validator = CantShareEmailValidator(users)
    user = SimpleNamespace(id=10)
    changeset = SimpleNamespace(new_email="unique@example.com")

    validator.validate(user, changeset)

    users.query.filter.return_value.count.assert_called_once_with()


def test_cant_share_email_rejects_registered_email():
    users = Mock()
    users.query.filter.return_value.count.return_value = 1

    validator = CantShareEmailValidator(users)
    user = SimpleNamespace(id=10)
    changeset = SimpleNamespace(new_email="used@example.com")

    with pytest.raises(ValidationError):
        validator.validate(user, changeset)
