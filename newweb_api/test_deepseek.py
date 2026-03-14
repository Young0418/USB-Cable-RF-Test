from deepseek_client import DeepSeekClient

def test_deepseek_api():
    """测试DeepSeek API"""
    print("正在测试DeepSeek API...")
    
    client = DeepSeekClient("sk-c286d401dae142318838f0119342b2bd")
    
    # 测试连接
    success, message = client.test_connection()
    print(f"连接测试: {'成功' if success else '失败'}")
    print(f"返回消息: {message}")
    
    if success:
        # 测试分析功能
        print("\n测试分析功能...")
        test_result = {
            "cable_type": "RG316",
            "qualified": True,
            "s11_qualified": True,
            "s21_qualified": True,
            "analysis_detail": {
                "s11_mean": -25.5,
                "s21_mean": -2.1
            }
        }
        
        analysis = client.analyze_cable_data(test_result, "这个线缆的性能如何？")
        print(f"分析结果: {analysis}")

if __name__ == "__main__":
    test_deepseek_api()