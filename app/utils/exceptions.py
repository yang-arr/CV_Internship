from typing import Optional, Dict, Any


class APIException(Exception):
    """
    API异常的基类
    """
    def __init__(
        self, 
        status_code: int, 
        detail: str, 
        error_code: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.data = data
        super().__init__(detail)


class ImageProcessingException(APIException):
    """
    图像处理异常
    """
    def __init__(
        self, 
        detail: str, 
        status_code: int = 400, 
        error_code: str = "image_processing_error",
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail, error_code, data)


class ModelInferenceException(APIException):
    """
    模型推理异常
    """
    def __init__(
        self, 
        detail: str, 
        status_code: int = 500, 
        error_code: str = "model_inference_error",
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail, error_code, data)


class DatabaseException(APIException):
    """
    数据库操作异常
    """
    def __init__(
        self, 
        detail: str, 
        status_code: int = 500, 
        error_code: str = "database_error",
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail, error_code, data)


class AuthenticationException(APIException):
    """
    认证异常
    """
    def __init__(
        self, 
        detail: str = "认证失败", 
        status_code: int = 401, 
        error_code: str = "authentication_error",
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail, error_code, data)


class AuthorizationException(APIException):
    """
    授权异常
    """
    def __init__(
        self, 
        detail: str = "没有操作权限", 
        status_code: int = 403, 
        error_code: str = "authorization_error",
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail, error_code, data)


class ResourceNotFoundException(APIException):
    """
    资源不存在异常
    """
    def __init__(
        self, 
        detail: str = "资源不存在", 
        status_code: int = 404, 
        error_code: str = "resource_not_found",
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail, error_code, data)


class ValidationException(APIException):
    """
    数据验证异常
    """
    def __init__(
        self, 
        detail: str, 
        status_code: int = 422, 
        error_code: str = "validation_error",
        data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code, detail, error_code, data) 