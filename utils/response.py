from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

#把所有接口的返回数据,统一包装成前端约定的 {code, message, data} 格式,并以 JSON 响应返回。
def success_response(message: str ="success",data =None):
    content = {
        "code": 200,
        "message": message,
        "data": data
    }

    #目标：把任何的FastAPI,Pydantic,ORM 对象都要正常响应 ——> code、message、data
    return JSONResponse(content=jsonable_encoder(content))