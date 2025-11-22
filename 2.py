import screen_brightness_control as sbc
import sys

def set_max_brightness_windows():
    try:
        # 获取当前亮度
        current_brightness = sbc.get_brightness()
        print(f"当前亮度: {current_brightness}%")
        
        # 设置亮度为100%
        sbc.set_brightness(100)
        
        # 验证设置
        new_brightness = sbc.get_brightness()
        print(f"亮度已设置为: {new_brightness}%")
        
    except Exception as e:
        print(f"设置亮度时出错: {e}")
        print("请确保已安装 screen-brightness-control 库")

if __name__ == "__main__":
    set_max_brightness_windows()