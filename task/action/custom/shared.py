from shlex import quote
from typing import Any

from conf.commerce_config import commerce_config
from infrastructure import http_client


def _base_url()->str:
    """
    组装URL
    :return:
    """
    return commerce_config.commerce_api_base_url.rstrip("/")


def _extract_data(result:dict[str,Any] | None) ->dict[str,Any] | None:
    """
    解析结果数据
    :param result:
    :return:
    """
    data = result.get("data") if isinstance(result,dict) else None
    return data if isinstance(data,dict) else None

async def fetch_order(order_id:str)->dict[str,Any] | None:
    """
    调用中台接口 获取订单信息
    :param order_id:
    :return:
    """
    try:
        r = await http_client.http_client.get(f"{_base_url()}/orders/{quote(order_id)}")
        return _extract_data(r.json())
    except Exception as e:
        print(e)
        return None

async def fetch_logistics(order_id:str)->dict[str,Any] | None:
    """
    调用中台接口 获取物流信息
    :param order_id:
    :return:
    """
    try:
        r = await http_client.http_client.get(f"{_base_url()}/orders/{quote(order_id)}/logistics")
        return _extract_data(r.json())
    except Exception as e:
        print(e)
        return None

async def fetch_product(product_id:str)->dict[str,Any] | None:
    """
    调用中台接口 获取推荐商品信息
    :param product_id:
    :return:
    """
    try:
        r = await http_client.get(f"{_base_url()}/products/{quote(product_id)}")
        return _extract_data(r.json())
    except Exception as e:
        print(e)
        return None

def _build_order_summary(payload: dict[str, Any]) -> str:
    parts = []
    if payload.get("amount"):
        parts.append(f"订单金额 ¥{payload['amount']}")
    items = payload.get("items") or []
    if items:
        titles = [str(item.get("title") or "").strip()
                  for item in items[:2] if item.get("title")]
        if titles:
            parts.append("商品：" + "、".join(titles))
    return "。".join(parts) + "。" if parts else ""

