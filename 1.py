import cv2
import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
import subprocess

class VideoToASCII:
    def __init__(self):
        # ASCII字符集，从暗到亮排列
        self.ascii_chars = "@%#*+=-:. "
        # 或者使用这个更丰富的字符集
        # self.ascii_chars = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
        
    def get_video_info(self, video_path):
        """获取视频信息并自动适配参数"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("无法打开视频文件")
        
        # 获取视频基本信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps
        
        print(f"视频信息:")
        print(f"  分辨率: {width}x{height}")
        print(f"  帧率: {fps:.2f} FPS")
        print(f"  总帧数: {total_frames}")
        print(f"  时长: {duration:.2f} 秒")
        
        # 自动计算输出尺寸 - 保持宽高比的同时缩小尺寸
        target_width = 120  # 输出ASCII艺术的宽度（字符数）
        scale_factor = target_width / width
        output_width = target_width
        output_height = int(height * scale_factor * 0.55)  # 0.55是字符的宽高比补偿
        
        # 确保高度是偶数，避免处理时的对齐问题
        output_height = output_height if output_height % 2 == 0 else output_height + 1
        
        print(f"输出尺寸: {output_width}x{output_height} 字符")
        
        cap.release()
        return {
            'fps': fps,
            'total_frames': total_frames,
            'original_width': width,
            'original_height': height,
            'output_width': output_width,
            'output_height': output_height,
            'duration': duration
        }
    
    def resize_frame(self, frame, new_width, new_height):
        """调整帧尺寸"""
        return cv2.resize(frame, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    def pixel_to_ascii(self, pixel_value):
        """将像素值转换为ASCII字符"""
        # 将像素值映射到ASCII字符集的索引
        char_index = int(pixel_value / 255 * (len(self.ascii_chars) - 1))
        return self.ascii_chars[char_index]
    
    def frame_to_ascii(self, frame):
        """将一帧转换为ASCII艺术"""
        # 转换为灰度图
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        ascii_art = ""
        for i in range(gray_frame.shape[0]):
            for j in range(gray_frame.shape[1]):
                ascii_art += self.pixel_to_ascii(gray_frame[i, j])
            ascii_art += "\n"
        
        return ascii_art
    
    def frame_to_ascii_image(self, frame, output_width, output_height, font_size=8):
        """将帧转换为ASCII艺术图像（用于保存为视频）"""
        # 调整尺寸
        resized_frame = self.resize_frame(frame, output_width, output_height)
        gray_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2GRAY)
        
        # 创建PIL图像
        img_width = output_width * font_size
        img_height = output_height * font_size
        ascii_image = Image.new('RGB', (img_width, img_height), color='black')
        draw = ImageDraw.Draw(ascii_image)
        
        # 尝试加载字体
        try:
            font = ImageFont.truetype("Courier.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("cour.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # 绘制ASCII字符
        y = 0
        for i in range(gray_frame.shape[0]):
            line = ""
            for j in range(gray_frame.shape[1]):
                line += self.pixel_to_ascii(gray_frame[i, j])
            
            draw.text((0, y), line, font=font, fill='white')
            y += font_size
        
        # 转换回OpenCV格式
        return cv2.cvtColor(np.array(ascii_image), cv2.COLOR_RGB2BGR)
    
    def process_video_to_text(self, video_path, output_txt=None, max_frames=None):
        """处理视频并输出为文本文件"""
        video_info = self.get_video_info(video_path)
        cap = cv2.VideoCapture(video_path)
        
        output_width = video_info['output_width']
        output_height = video_info['output_height']
        
        if output_txt is None:
            output_txt = os.path.splitext(video_path)[0] + "_ascii.txt"
        
        frame_count = 0
        with open(output_txt, 'w', encoding='utf-8') as f:
            while True:
                ret, frame = cap.read()
                if not ret or (max_frames and frame_count >= max_frames):
                    break
                
                # 调整尺寸并转换为ASCII
                resized_frame = self.resize_frame(frame, output_width, output_height)
                ascii_art = self.frame_to_ascii(resized_frame)
                
                # 写入分隔符和ASCII艺术
                f.write(f"=== Frame {frame_count} ===\n")
                f.write(ascii_art)
                f.write("\n" + "="*50 + "\n\n")
                
                frame_count += 1
                if frame_count % 30 == 0:
                    print(f"已处理 {frame_count}/{video_info['total_frames']} 帧")
        
        cap.release()
        print(f"ASCII文本已保存到: {output_txt}")
        return output_txt
    
    def process_video_to_video(self, video_path, output_video=None, max_frames=None):
        """处理视频并输出为新的ASCII艺术视频"""
        video_info = self.get_video_info(video_path)
        cap = cv2.VideoCapture(video_path)
        
        output_width = video_info['output_width']
        output_height = video_info['output_height']
        
        if output_video is None:
            output_video = os.path.splitext(video_path)[0] + "_ascii.mp4"
        
        # 设置输出视频参数
        font_size = 8
        video_width = output_width * font_size
        video_height = output_height * font_size
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video, fourcc, video_info['fps'], 
                             (video_width, video_height))
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret or (max_frames and frame_count >= max_frames):
                break
            
            # 转换为ASCII艺术图像
            ascii_frame = self.frame_to_ascii_image(frame, output_width, output_height, font_size)
            out.write(ascii_frame)
            
            frame_count += 1
            if frame_count % 30 == 0:
                print(f"已处理 {frame_count}/{video_info['total_frames']} 帧")
        
        cap.release()
        out.release()
        print(f"ASCII视频已保存到: {output_video}")
        return output_video
    
    def preview_ascii_animation(self, video_path, max_frames=100, delay=50):
        """在控制台预览ASCII动画"""
        video_info = self.get_video_info(video_path)
        cap = cv2.VideoCapture(video_path)
        
        output_width = 80  # 控制台预览使用固定宽度
        scale_factor = output_width / video_info['original_width']
        output_height = int(video_info['original_height'] * scale_factor * 0.55)
        
        frame_count = 0
        try:
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 调整尺寸并转换为ASCII
                resized_frame = self.resize_frame(frame, output_width, output_height)
                ascii_art = self.frame_to_ascii(resized_frame)
                
                # 清屏并显示新帧（Windows和Unix兼容）
                os.system('cls' if os.name == 'nt' else 'clear')
                print(ascii_art)
                print(f"帧: {frame_count}/{min(max_frames, video_info['total_frames'])}")
                print("按Ctrl+C停止预览")
                
                frame_count += 1
                cv2.waitKey(delay)
                
        except KeyboardInterrupt:
            print("\n预览已停止")
        
        cap.release()

def main():
    converter = VideoToASCII()
    
    # 输入视频路径
    video_path = input("请输入视频文件路径: ").strip().strip('"')
    
    if not os.path.exists(video_path):
        print("视频文件不存在!")
        return
    
    print("\n选择输出模式:")
    print("1. 文本文件 (.txt)")
    print("2. ASCII艺术视频 (.mp4)")
    print("3. 控制台预览")
    
    choice = input("请输入选择 (1/2/3): ").strip()
    
    try:
        if choice == '1':
            max_frames = input("最大处理帧数 (直接回车处理全部): ").strip()
            max_frames = int(max_frames) if max_frames else None
            converter.process_video_to_text(video_path, max_frames=max_frames)
            
        elif choice == '2':
            max_frames = input("最大处理帧数 (直接回车处理全部): ").strip()
            max_frames = int(max_frames) if max_frames else None
            converter.process_video_to_video(video_path, max_frames=max_frames)
            
        elif choice == '3':
            max_frames = input("预览帧数 (默认100): ").strip()
            max_frames = int(max_frames) if max_frames else 100
            delay = input("帧延迟ms (默认50): ").strip()
            delay = int(delay) if delay else 50
            converter.preview_ascii_animation(video_path, max_frames=max_frames, delay=delay)
            
        else:
            print("无效选择!")
            
    except Exception as e:
        print(f"处理过程中出错: {e}")

if __name__ == "__main__":
    main()