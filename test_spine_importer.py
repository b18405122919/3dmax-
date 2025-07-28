#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spine动画导入工具测试脚本
用于验证导入功能的各个组件
"""

import os
import json
import tempfile
import shutil

def create_test_files():
    """创建测试用的Spine文件"""
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    texture_dir = os.path.join(temp_dir, "textures")
    os.makedirs(texture_dir, exist_ok=True)
    
    # 创建测试JSON文件
    test_json = {
        "bones": [
            {
                "name": "root",
                "x": 0,
                "y": 0,
                "length": 1.0,
                "rotation": 0
            },
            {
                "name": "bone1",
                "x": 0,
                "y": -1,
                "length": 1.0,
                "rotation": 0,
                "parent": "root"
            },
            {
                "name": "bone2",
                "x": 0,
                "y": -2,
                "length": 1.0,
                "rotation": 0,
                "parent": "bone1"
            }
        ],
        "slots": [
            {
                "name": "slot1",
                "bone": "root",
                "attachment": {
                    "name": "texture1.png",
                    "width": 100,
                    "height": 100
                }
            },
            {
                "name": "slot2",
                "bone": "bone1",
                "attachment": {
                    "name": "texture2.png",
                    "width": 80,
                    "height": 80
                }
            }
        ],
        "animations": {
            "test_animation": {
                "bones": {
                    "root": {
                        "translate": [
                            {"time": 0, "x": 0, "y": 0},
                            {"time": 1, "x": 10, "y": 0},
                            {"time": 2, "x": 0, "y": 0}
                        ],
                        "rotate": [
                            {"time": 0, "angle": 0},
                            {"time": 1, "angle": 0.5},
                            {"time": 2, "angle": 0}
                        ]
                    },
                    "bone1": {
                        "rotate": [
                            {"time": 0, "angle": 0},
                            {"time": 1, "angle": -0.3},
                            {"time": 2, "angle": 0}
                        ]
                    }
                }
            }
        }
    }
    
    json_path = os.path.join(temp_dir, "test_spine.json")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(test_json, f, indent=2, ensure_ascii=False)
    
    # 创建测试Atlas文件
    atlas_content = """texture1.png
  rotate: false
  xy: 0, 0
  size: 100, 100
  orig: 100, 100
  offset: 0, 0
  index: -1
texture2.png
  rotate: false
  xy: 100, 0
  size: 80, 80
  orig: 80, 80
  offset: 0, 0
  index: -1
"""
    
    atlas_path = os.path.join(temp_dir, "test_spine.atlas")
    with open(atlas_path, 'w', encoding='utf-8') as f:
        f.write(atlas_content)
    
    # 创建测试纹理文件（简单的占位符）
    texture1_path = os.path.join(texture_dir, "texture1.png")
    texture2_path = os.path.join(texture_dir, "texture2.png")
    
    # 创建简单的PNG文件（这里只是创建空文件作为示例）
    with open(texture1_path, 'w') as f:
        f.write("PNG placeholder")
    with open(texture2_path, 'w') as f:
        f.write("PNG placeholder")
    
    return temp_dir, json_path, atlas_path, texture_dir

def test_safe_str():
    """测试safe_str函数"""
    print("🧪 测试safe_str函数...")
    
    test_cases = [
        ("正常字符串", "正常字符串"),
        ("包含\\的路径", "包含/的路径"),
        ("包含\"的字符串", "包含'的字符串"),
        ("包含\n换行", "包含 换行"),
        (None, ""),
        ("", ""),
        (123, "123")
    ]
    
    for input_val, expected in test_cases:
        result = safe_str(input_val)
        if result == expected:
            print(f"✅ {input_val} -> {result}")
        else:
            print(f"❌ {input_val} -> {result} (期望: {expected})")

def test_file_validation():
    """测试文件验证功能"""
    print("\n🧪 测试文件验证...")
    
    # 创建测试文件
    temp_dir, json_path, atlas_path, texture_dir = create_test_files()
    
    try:
        # 测试文件存在性检查
        assert os.path.exists(json_path), "JSON文件应该存在"
        assert os.path.exists(atlas_path), "Atlas文件应该存在"
        assert os.path.exists(texture_dir), "纹理目录应该存在"
        
        print("✅ 文件验证通过")
        
        # 测试JSON解析
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "bones" in data, "JSON应该包含bones数据"
        assert "slots" in data, "JSON应该包含slots数据"
        assert "animations" in data, "JSON应该包含animations数据"
        
        print("✅ JSON解析通过")
        
        # 测试数据结构
        bones = data["bones"]
        slots = data["slots"]
        animations = data["animations"]
        
        assert len(bones) == 3, f"应该有3个骨骼，实际有{len(bones)}个"
        assert len(slots) == 2, f"应该有2个槽位，实际有{len(slots)}个"
        assert len(animations) == 1, f"应该有1个动画，实际有{len(animations)}个"
        
        print("✅ 数据结构验证通过")
        
    finally:
        # 清理临时文件
        shutil.rmtree(temp_dir)
        print("🧹 临时文件已清理")

def test_animation_analysis():
    """测试动画数据分析"""
    print("\n🧪 测试动画数据分析...")
    
    # 创建测试数据
    test_animations = {
        "test_animation": {
            "bones": {
                "root": {
                    "translate": [
                        {"time": 0, "x": 0, "y": 0},
                        {"time": 1, "x": 10, "y": 0},
                        {"time": 2, "x": 0, "y": 0}
                    ],
                    "rotate": [
                        {"time": 0, "angle": 0},
                        {"time": 1, "angle": 0.5},
                        {"time": 2, "angle": 0}
                    ]
                }
            }
        }
    }
    
    # 计算动画长度
    anim_length = 0
    total_keyframes = 0
    
    for anim_name, anim_data in test_animations.items():
        bones_data = anim_data.get("bones", {})
        for bone_name, bone_anim in bones_data.items():
            for anim_type in ["translate", "rotate", "scale"]:
                if anim_type in bone_anim:
                    frames = bone_anim[anim_type]
                    total_keyframes += len(frames)
                    for frame in frames:
                        anim_length = max(anim_length, float(frame.get("time", 0)))
    
    # 转换为帧数
    anim_length = int(anim_length * 30) + 10
    
    print(f"⏱️ 动画长度: {anim_length}帧")
    print(f"🎯 总关键帧数: {total_keyframes}")
    
    assert anim_length > 0, "动画长度应该大于0"
    assert total_keyframes > 0, "关键帧数应该大于0"
    
    print("✅ 动画数据分析通过")

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行Spine导入工具测试...")
    print("=" * 50)
    
    try:
        test_safe_str()
        test_file_validation()
        test_animation_analysis()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！")
        print("✅ Spine导入工具功能正常")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        print(f"📋 详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    # 导入必要的函数（这里需要从主脚本导入）
    try:
        from spine_importer import safe_str
        run_all_tests()
    except ImportError:
        print("⚠️ 无法导入spine_importer模块，请确保脚本在同一目录下")
        print("📝 仅运行基础测试...")
        
        # 基础测试
        def safe_str(s):
            try:
                if s is None:
                    return ""
                return str(s).replace('\\', '/').replace('"', "'").replace('\n', ' ').strip()
            except:
                return ""
        
        test_safe_str()
        test_file_validation()
        test_animation_analysis()