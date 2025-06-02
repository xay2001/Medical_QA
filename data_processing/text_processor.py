import jieba
import jieba.analyse
import re
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import sys

# 添加Django环境
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from qa_system.models import QAData

class TextProcessor:
    def __init__(self):
        # 中文停用词表
        self.stop_words = set([
            '的', '了', '是', '在', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你',
            '会', '着', '没有', '看', '好', '自己', '这', '那', '还', '能', '下', '过', '他', '来', '对', '开始', '地', '可以',
            '什么', '现在', '一些', '最', '这个', '我', '们', '后', '中', '多', '么', '用', '同', '回', '当', '没', '动', '怎么',
            '又', '如', '被', '从', '做', '他们', '她', '但', '或者', '已经', '还是', '因为', '所以', '虽然', '然后', '而且',
            '比如', '等等', '可能', '应该', '需要', '进行', '之后', '通过', '关于', '由于', '根据', '这样', '那样', '这里',
            '那里', '这些', '那些', '每个', '任何', '所有', '另外', '其他', '同时', '然而', '因此', '于是', '接着', '首先',
            '其次', '最后', '总之', '一般', '特别', '尤其', '包括', '除了', '如果', '虽然', '但是', '只是', '不过', '当然',
            '确实', '实际', '基本', '主要', '重要', '必须', '一定', '可能', '也许', '或许', '大概', '差不多', '几乎', '完全'
        ])
        
        # 医疗相关停用词
        self.medical_stop_words = set([
            '患者', '病人', '医生', '大夫', '医院', '诊断', '治疗', '检查', '化验', '症状', '疾病', '药物', '服用',
            '建议', '注意', '预防', '护理', '康复', '保健', '健康'
        ])
        
        self.stop_words.update(self.medical_stop_words)
        
        # 初始化jieba
        jieba.initialize()
        
        # 添加医疗词汇
        self.add_medical_words()
    
    def add_medical_words(self):
        """添加医疗专业词汇到jieba词典"""
        medical_words = [
            '高血压', '糖尿病', '心脏病', '脑血管', '冠心病', '心肌梗塞', '脑梗塞', '脑出血',
            '肺炎', '肺结核', '哮喘', '支气管炎', '肺癌', '胃炎', '胃溃疡', '肠炎', '胆结石',
            '肾结石', '尿路感染', '前列腺', '乳腺癌', '宫颈癌', '骨质疏松', '关节炎', '风湿',
            '甲状腺', '内分泌', '免疫力', '过敏性', '传染性', '慢性病', '急性病', '并发症',
            '副作用', '不良反应', '药物相互作用', '抗生素', '消炎药', '止痛药', '降压药',
            '降糖药', '胰岛素', '维生素', '钙片', '叶酸', '血常规', '尿常规', 'B超', 'CT',
            'MRI', 'X光', '心电图', '血压', '血糖', '血脂', '胆固醇', '白细胞', '红细胞',
            '血小板', '血红蛋白', '肝功能', '肾功能', '心功能', '肺功能'
        ]
        
        for word in medical_words:
            jieba.add_word(word)
    
    def segment_text(self, text):
        """中文分词"""
        if not text:
            return []
        
        # 清理文本
        text = self.clean_text(text)
        
        # 分词
        words = jieba.cut(text)
        
        # 过滤停用词和短词
        filtered_words = []
        for word in words:
            word = word.strip()
            if len(word) > 1 and word not in self.stop_words and word.isalnum():
                filtered_words.append(word)
        
        return filtered_words
    
    def clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除特殊字符，保留中文、英文、数字和基本标点
        text = re.sub(r'[^\w\s\u4e00-\u9fff，。？！；：""''（）【】、]', '', text)
        
        return text
    
    def extract_keywords(self, text, num_keywords=10):
        """提取关键词"""
        if not text:
            return []
        
        # 使用jieba的TF-IDF提取关键词
        keywords_tfidf = jieba.analyse.extract_tags(text, topK=num_keywords, withWeight=True)
        
        # 使用jieba的TextRank提取关键词
        keywords_textrank = jieba.analyse.textrank(text, topK=num_keywords, withWeight=True)
        
        # 合并并去重
        all_keywords = {}
        
        for word, weight in keywords_tfidf:
            all_keywords[word] = weight
        
        for word, weight in keywords_textrank:
            if word in all_keywords:
                all_keywords[word] = (all_keywords[word] + weight) / 2
            else:
                all_keywords[word] = weight
        
        # 按权重排序
        sorted_keywords = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, weight in sorted_keywords[:num_keywords]]
    
    def process_qa_data(self, qa_id=None):
        """处理问答数据"""
        if qa_id:
            qa_objects = QAData.objects.filter(id=qa_id)
        else:
            qa_objects = QAData.objects.filter(processed_question='', processed_answer='')
        
        processed_count = 0
        
        for qa in qa_objects:
            try:
                # 处理问题
                question_words = self.segment_text(qa.question)
                processed_question = ' '.join(question_words)
                
                # 处理答案
                answer_words = self.segment_text(qa.answer)
                processed_answer = ' '.join(answer_words)
                
                # 提取关键词
                combined_text = qa.question + ' ' + qa.answer
                keywords = self.extract_keywords(combined_text)
                
                # 更新数据库
                qa.processed_question = processed_question
                qa.processed_answer = processed_answer
                qa.set_keywords_list(keywords)
                qa.save()
                
                processed_count += 1
                
                if processed_count % 100 == 0:
                    print(f"已处理 {processed_count} 条数据")
                    
            except Exception as e:
                print(f"处理数据 {qa.id} 失败: {e}")
                continue
        
        print(f"数据预处理完成，共处理 {processed_count} 条数据")
        return processed_count
    
    def build_index(self):
        """构建倒排索引"""
        print("正在构建文本索引...")
        
        # 获取所有已处理的问答数据
        qa_objects = QAData.objects.exclude(processed_question='')
        
        # 构建文档集合
        documents = []
        document_ids = []
        
        for qa in qa_objects:
            # 合并问题和答案作为一个文档
            doc_text = qa.processed_question + ' ' + qa.processed_answer
            documents.append(doc_text)
            document_ids.append(qa.id)
        
        if not documents:
            print("没有找到已处理的文档")
            return None
        
        # 使用TF-IDF构建索引
        vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        # 保存索引信息
        index_info = {
            'vectorizer': vectorizer,
            'tfidf_matrix': tfidf_matrix,
            'document_ids': document_ids
        }
        
        print(f"索引构建完成，共索引 {len(documents)} 个文档")
        return index_info
    
    def search_similar_qa(self, query, index_info, top_k=5):
        """搜索相似的问答"""
        if not index_info:
            return []
        
        vectorizer = index_info['vectorizer']
        tfidf_matrix = index_info['tfidf_matrix']
        document_ids = index_info['document_ids']
        
        # 处理查询文本
        query_words = self.segment_text(query)
        processed_query = ' '.join(query_words)
        
        # 向量化查询
        query_vector = vectorizer.transform([processed_query])
        
        # 计算相似度
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # 获取最相似的文档
        top_indices = similarities.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if similarities[idx] > 0:  # 只返回有相似度的结果
                qa_id = document_ids[idx]
                qa = QAData.objects.get(id=qa_id)
                results.append({
                    'qa': qa,
                    'similarity': float(similarities[idx])
                })
        
        return results

def main():
    """测试数据预处理功能"""
    processor = TextProcessor()
    
    print("开始数据预处理...")
    processed_count = processor.process_qa_data()
    
    print("\n构建文本索引...")
    index_info = processor.build_index()
    
    if index_info:
        print("\n测试搜索功能...")
        query = "感冒发烧怎么办"
        results = processor.search_similar_qa(query, index_info)
        
        print(f"查询: {query}")
        print("搜索结果:")
        for i, result in enumerate(results, 1):
            qa = result['qa']
            similarity = result['similarity']
            print(f"{i}. 相似度: {similarity:.3f}")
            print(f"   问题: {qa.question[:50]}...")
            print(f"   答案: {qa.answer[:50]}...")
            print()

if __name__ == "__main__":
    main() 