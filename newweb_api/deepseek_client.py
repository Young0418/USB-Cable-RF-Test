import logging
import os
import requests
from typing import Dict, Tuple

logger = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: int = 20):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DeepSeek API key 未配置")

        self.base_url = base_url or "https://api.deepseek.com/v1/chat/completions"
        self.timeout = timeout
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def analyze_cable_data(self, analysis_result: dict, user_question: str = "") -> str:
        cable_type = analysis_result.get("cable_type", "未知")
        qualified = analysis_result.get("qualified", False)
        s11_qualified = analysis_result.get("s11_qualified", False)
        s21_qualified = analysis_result.get("s21_qualified", False)
        detail = analysis_result.get("analysis_detail", {})
        s11_mean = detail.get("s11_mean", 0)
        s21_mean = detail.get("s21_mean", 0)

        if not user_question.strip():
            user_question = "请用两句话总结这次检测结果，并给操作建议"

        system_prompt = (
            "你是资深线缆检测工程师。请使用官方口吻、80字以内回答，"
            "聚焦合格与否、可否出货、下一步建议。"
        )
        data_prompt = (
            f"线缆: {cable_type}\n整体: {'合格' if qualified else '不合格'}\n"
            f"S11: {s11_mean:.2f}dB ({'合格' if s11_qualified else '不合格'})\n"
            f"S21: {s21_mean:.2f}dB ({'合格' if s21_qualified else '不合格'})\n"
        )

        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": data_prompt + "\n问题：" + user_question},
            ],
            "max_tokens": 90,
            "temperature": 0.25,
            "stream": False,
        }

        try:
            resp = self.session.post(
                self.base_url, headers=self._headers(), json=payload, timeout=self.timeout
            )
            if resp.status_code != 200:
                error_text = self._safe_error(resp)
                raise RuntimeError(f"HTTP {resp.status_code}: {error_text}")
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except requests.exceptions.Timeout:
            raise RuntimeError("AI请求超时")
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"AI请求失败: {exc}") from exc

    def test_connection(self) -> Tuple[bool, str]:
        payload = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": "请回复：连接成功"}],
            "max_tokens": 10,
            "temperature": 0.2,
        }
        try:
            resp = self.session.post(
                self.base_url, headers=self._headers(), json=payload, timeout=10
            )
            if resp.status_code == 200:
                reply = resp.json()["choices"][0]["message"]["content"].strip()
                return True, reply
            return False, self._safe_error(resp)
        except requests.exceptions.RequestException as exc:
            return False, f"网络错误: {exc}"

    @staticmethod
    def _safe_error(response: requests.Response) -> str:
        try:
            return response.json().get("error", {}).get("message", response.text)
        except Exception:
            return response.text[:120]