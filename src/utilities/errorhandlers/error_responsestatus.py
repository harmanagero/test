from src.models.domain.enums.internal_status_type import InternalStatusType
from src.models.exceptions.application_exception import ApplicationException
from src.models.exceptions.badrequest_exception import BadRequestException
from src.models.exceptions.forbidden_exception import ForbiddenException
from src.models.exceptions.notfound_exception import NotFoundException


def handle_error_responsestatus(responsestatus):
    # responsestatus value can be of any case, which is handled here by casefold
    responsestatus = responsestatus.casefold()
    switcher = {
        InternalStatusType.BADREQUEST.casefold(): BadRequestException,
        InternalStatusType.FORBIDDEN.casefold(): ForbiddenException,
        InternalStatusType.NOTFOUND.casefold(): NotFoundException,
        InternalStatusType.INTERNALSERVERERROR.casefold(): ApplicationException,
    }
    return switcher.get(responsestatus, ApplicationException)
