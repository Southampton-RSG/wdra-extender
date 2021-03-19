import typing
import werkzeug


# Tools for validating tweet ids =======================================================================================
class ValidationError(werkzeug.exceptions.BadRequest):
    """Error in validating user-provided data."""
    code = 400
    description = 'Invalid data provided.'


def cast_tweet_id(tweet_id: str) -> int:
    """Cast a single Tweet ID to int.

    They may be prefixed with 'ID:' so try to remove this.
    """
    if tweet_id.lower().startswith('id:'):
        tweet_id = tweet_id.lower()[3:]

    return int(tweet_id)


def validate_tweet_ids(tweet_ids: typing.Iterable[str]) -> typing.List[int]:
    """Cast Tweet IDs to integer or raise ValidationError."""

    if not tweet_ids:
        raise ValidationError('No Tweet IDs were found.')

    try:
        # Filter out blank lines and cast to int
        return [cast_tweet_id(tweet_id) for tweet_id in tweet_ids if tweet_id.strip()]

    except ValueError as exc:
        raise ValidationError('Tweet IDs must be integers.') from exc
# ======================================================================================================================
