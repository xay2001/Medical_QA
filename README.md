# 医疗知识问答系统

基于Django和PaddleOCR的智能医疗问答系统，支持文本问答、图像识别、文档分析和文本挖掘功能。

## 功能特点

1. **智能问答**
   - 基于丁香医生数据的医疗问答
   - 实时对话交互
   - 智能建议生成

2. **图像识别**
   - 医疗图像OCR文字识别
   - 医学实体识别（疾病、症状、药物、检查、治疗）
   - 智能医疗建议生成

3. **文档处理**
   - 支持多种格式（TXT、PDF、DOCX）
   - 词性标注和实体识别
   - 文档摘要生成

4. **文本挖掘**
   - 数据集聚类分析
   - t-SNE可视化
   - 词云图生成

## 技术栈

- 后端：Django 3.2
- OCR：PaddleOCR 3.0
- 前端：Bootstrap 5.1
- 数据库：SQLite3

## 项目结构

```
medical_qa_system/
├── backend/                 # Django项目配置
├── qa_system/              # 主应用模块
│   ├── models.py           # 数据模型
│   ├── views.py           # 视图函数
│   ├── urls.py            # URL路由
│   └── migrations/        # 数据库迁移
├── image_recognition/      # 图像识别模块
│   └── medical_ocr.py     # OCR处理类
├── text_mining/           # 文本挖掘模块
│   └── text_mining_analyzer.py
├── data_processing/       # 数据处理模块
│   └── text_processor.py
├── crawler/              # 数据爬取模块
│   └── dingxiang_crawler.py
├── templates/            # 前端模板
│   ├── index.html       # 主页面
│   └── dashboard.html   # 监控面板
├── tests/               # 测试相关
│   ├── test_api.py     # API测试
│   ├── test_ocr.py     # OCR测试
│   ├── test_new_features.py
│   ├── create_test_image.py
│   ├── create_medical_test_image.py
│   ├── data/           # 测试数据
│   └── images/         # 测试图片
├── media/              # 上传文件存储
├── manage.py           # Django管理脚本
├── requirements.txt    # 项目依赖
└── README.md          # 项目文档
```

## 安装说明

1. 克隆项目
```bash
git clone https://github.com/xay2001/Medical_QA.git
cd Medical_QA
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 初始化数据库
```bash
python manage.py makemigrations
python manage.py migrate
```

4. 启动服务器
```bash
python manage.py runserver
```

## 使用说明

1. 访问 http://localhost:8000 打开系统主页
2. 在智能问答区域输入医疗相关问题
3. 使用图像识别功能上传医疗图像进行分析
4. 在文档处理区域上传医疗文档进行分析
5. 使用文本挖掘功能分析医疗数据集

## 注意事项

- 本系统提供的信息仅供参考，不能替代专业医疗诊断
- 首次使用时会自动下载PaddleOCR模型文件
- 建议使用Chrome或Firefox浏览器访问

## 许可证

MIT License

## 更新日志

### v1.0.0 (2024-06-02)
- 完整的医疗问答系统实现
- 支持文本挖掘和可视化
- 系统监控仪表板
- 文档处理功能
- 13个医疗类别数据支持 