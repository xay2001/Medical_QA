import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # 设置非交互式后端
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans, DBSCAN
from sklearn.manifold import TSNE
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from wordcloud import WordCloud
import jieba
import json
import os
import sys
from datetime import datetime
import base64
from io import BytesIO

# 添加Django环境
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from qa_system.models import TextMiningResult, QAData
from data_processing.text_processor import TextProcessor

class TextMiningAnalyzer:
    def __init__(self):
        self.text_processor = TextProcessor()
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
    def load_dataset(self, file_path=None, use_qa_data=True):
        """加载数据集"""
        if use_qa_data:
            # 使用现有的问答数据
            qa_objects = QAData.objects.all()
            texts = []
            labels = []
            
            for qa in qa_objects:
                # 合并问题和答案
                combined_text = qa.question + " " + qa.answer
                texts.append(combined_text)
                labels.append(qa.category or "未分类")
                
            return texts, labels
        else:
            # 从文件加载数据集
            if file_path and os.path.exists(file_path):
                # 这里可以处理CSV、JSON等格式的文件
                pass
            return [], []
    
    def preprocess_texts(self, texts):
        """预处理文本数据"""
        processed_texts = []
        
        for text in texts:
            # 使用TextProcessor进行预处理
            words = self.text_processor.segment_text(text)
            processed_text = " ".join(words)
            processed_texts.append(processed_text)
            
        return processed_texts
    
    def perform_clustering(self, texts, method='kmeans', n_clusters=5):
        """执行文本聚类"""
        # 预处理文本
        processed_texts = self.preprocess_texts(texts)
        
        # TF-IDF向量化
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.8
        )
        
        tfidf_matrix = vectorizer.fit_transform(processed_texts)
        
        # 聚类算法
        if method == 'kmeans':
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        elif method == 'dbscan':
            clusterer = DBSCAN(eps=0.5, min_samples=5)
        else:
            raise ValueError("不支持的聚类方法")
        
        cluster_labels = clusterer.fit_predict(tfidf_matrix.toarray())
        
        # 分析聚类结果
        cluster_info = self.analyze_clusters(texts, cluster_labels, vectorizer, tfidf_matrix)
        
        return {
            'cluster_labels': cluster_labels.tolist(),
            'cluster_info': cluster_info,
            'n_clusters': len(set(cluster_labels)) if method == 'dbscan' else n_clusters,
            'method': method
        }
    
    def analyze_clusters(self, texts, cluster_labels, vectorizer, tfidf_matrix):
        """分析聚类结果"""
        cluster_info = {}
        feature_names = vectorizer.get_feature_names_out()
        
        for cluster_id in set(cluster_labels):
            if cluster_id == -1:  # DBSCAN的噪声点
                continue
                
            # 获取该簇的文档
            cluster_docs = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
            cluster_texts = [texts[i] for i in cluster_docs]
            
            # 计算该簇的TF-IDF均值
            cluster_tfidf = tfidf_matrix[cluster_docs].mean(axis=0).A1
            
            # 获取top关键词
            top_indices = cluster_tfidf.argsort()[-10:][::-1]
            top_keywords = [feature_names[i] for i in top_indices]
            
            cluster_info[f"簇_{cluster_id}"] = {
                'size': len(cluster_docs),
                'keywords': top_keywords,
                'sample_texts': cluster_texts[:3]  # 示例文档
            }
        
        return cluster_info
    
    def generate_tsne_visualization(self, texts, cluster_labels=None):
        """生成t-SNE可视化"""
        # 预处理和向量化
        processed_texts = self.preprocess_texts(texts)
        vectorizer = TfidfVectorizer(max_features=100, ngram_range=(1, 2))
        tfidf_matrix = vectorizer.fit_transform(processed_texts)
        
        # t-SNE降维
        tsne = TSNE(n_components=2, random_state=42, perplexity=30, n_iter=300)
        tsne_results = tsne.fit_transform(tfidf_matrix.toarray())
        
        # 创建可视化
        plt.figure(figsize=(12, 8))
        
        if cluster_labels is not None:
            # 按聚类结果着色
            unique_labels = list(set(cluster_labels))
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_labels)))
            
            for i, label in enumerate(unique_labels):
                if label == -1:  # 噪声点
                    color = 'black'
                    alpha = 0.5
                else:
                    color = colors[i]
                    alpha = 0.7
                
                mask = np.array(cluster_labels) == label
                plt.scatter(tsne_results[mask, 0], tsne_results[mask, 1], 
                           c=[color], alpha=alpha, s=50, 
                           label=f'簇 {label}' if label != -1 else '噪声')
        else:
            plt.scatter(tsne_results[:, 0], tsne_results[:, 1], alpha=0.7, s=50)
        
        plt.title('文本数据 t-SNE 可视化', fontsize=16)
        plt.xlabel('t-SNE 维度 1', fontsize=12)
        plt.ylabel('t-SNE 维度 2', fontsize=12)
        
        if cluster_labels is not None:
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        plt.tight_layout()
        
        # 保存图片到BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        
        # 转换为base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def generate_wordclouds(self, texts, cluster_labels=None, categories=None):
        """生成词云图"""
        wordcloud_results = {}
        
        if cluster_labels is not None:
            # 为每个聚类生成词云
            for cluster_id in set(cluster_labels):
                if cluster_id == -1:  # 跳过噪声点
                    continue
                
                cluster_texts = [texts[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                combined_text = " ".join(cluster_texts)
                processed_text = " ".join(self.text_processor.segment_text(combined_text))
                
                if processed_text.strip():
                    wordcloud_img = self.create_single_wordcloud(processed_text, f"簇_{cluster_id}")
                    wordcloud_results[f"cluster_{cluster_id}"] = wordcloud_img
        
        elif categories is not None:
            # 按类别生成词云
            category_texts = {}
            for text, category in zip(texts, categories):
                if category not in category_texts:
                    category_texts[category] = []
                category_texts[category].append(text)
            
            for category, cat_texts in category_texts.items():
                combined_text = " ".join(cat_texts)
                processed_text = " ".join(self.text_processor.segment_text(combined_text))
                
                if processed_text.strip():
                    wordcloud_img = self.create_single_wordcloud(processed_text, category)
                    wordcloud_results[category] = wordcloud_img
        
        else:
            # 生成整体词云
            combined_text = " ".join(texts)
            processed_text = " ".join(self.text_processor.segment_text(combined_text))
            
            if processed_text.strip():
                wordcloud_img = self.create_single_wordcloud(processed_text, "整体词云")
                wordcloud_results["overall"] = wordcloud_img
        
        return wordcloud_results
    
    def create_single_wordcloud(self, text, title):
        """创建单个词云图"""
        # 设置中文字体路径（适用于macOS）
        import platform
        font_path = None
        
        if platform.system() == 'Darwin':  # macOS
            # macOS系统中文字体路径
            possible_fonts = [
                '/System/Library/Fonts/PingFang.ttc',
                '/System/Library/Fonts/STHeiti Light.ttc',
                '/System/Library/Fonts/STHeiti Medium.ttc',
                '/Library/Fonts/Arial Unicode MS.ttf'
            ]
        elif platform.system() == 'Windows':  # Windows
            possible_fonts = [
                'C:/Windows/Fonts/simhei.ttf',
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simsun.ttc'
            ]
        else:  # Linux
            possible_fonts = [
                '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'
            ]
        
        # 找到第一个存在的字体文件
        for font in possible_fonts:
            if os.path.exists(font):
                font_path = font
                break
        
        # 创建词云
        wordcloud_params = {
            'width': 800,
            'height': 600,
            'background_color': 'white',
            'max_words': 100,
            'relative_scaling': 0.5,
            'colormap': 'viridis',
            'prefer_horizontal': 0.9
        }
        
        # 如果找到了中文字体，则添加字体路径
        if font_path:
            wordcloud_params['font_path'] = font_path
        
        wordcloud = WordCloud(**wordcloud_params).generate(text)
        
        # 创建图片
        plt.figure(figsize=(10, 6))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.title(f'{title} 词云图', fontsize=16)
        plt.axis('off')
        
        # 保存图片到BytesIO
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        
        # 转换为base64
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def run_complete_analysis(self, dataset_name="医疗问答数据", clustering_method='kmeans', n_clusters=5):
        """运行完整的文本挖掘分析（使用现有问答数据）"""
        try:
            # 加载数据
            texts, categories = self.load_dataset(use_qa_data=True)
            
            if not texts:
                raise ValueError("没有找到可用的数据")
            
            print(f"加载了 {len(texts)} 条文本数据")
            
            # 执行聚类分析
            clustering_result = self.perform_clustering(texts, method=clustering_method, n_clusters=n_clusters)
            
            # 生成可视化
            tsne_image = self.generate_tsne_visualization(texts, clustering_result['cluster_labels'])
            wordcloud_results = self.generate_wordclouds(texts, clustering_result['cluster_labels'])
            
            # 保存结果到数据库
            mining_result = TextMiningResult.objects.create(
                dataset_name=dataset_name,
                clustering_result=json.dumps(clustering_result),
                wordcloud_plots=json.dumps({
                    'tsne_image': tsne_image,
                    'wordclouds': wordcloud_results
                })
            )
            
            # 生成摘要
            summary = {
                'total_texts': len(texts),
                'n_clusters': clustering_result['n_clusters'],
                'clustering_method': clustering_method,
                'categories': len(set(categories)) if categories else 0
            }
            
            return {
                'result_id': mining_result.id,
                'summary': summary,
                'clustering': clustering_result,
                'tsne_image': tsne_image,
                'wordclouds': wordcloud_results
            }
            
        except Exception as e:
            print(f"文本挖掘分析错误: {e}")
            raise

    def run_complete_analysis_with_texts(self, texts, dataset_name="上传数据集", clustering_method='kmeans', n_clusters=5):
        """运行完整的文本挖掘分析（使用上传的文本数据）"""
        try:
            if not texts:
                raise ValueError("没有找到可用的数据")
            
            print(f"分析 {len(texts)} 条文本数据")
            
            # 执行聚类分析
            clustering_result = self.perform_clustering(texts, method=clustering_method, n_clusters=n_clusters)
            
            # 生成可视化
            tsne_image = self.generate_tsne_visualization(texts, clustering_result['cluster_labels'])
            wordcloud_results = self.generate_wordclouds(texts, clustering_result['cluster_labels'])
            
            # 保存结果到数据库
            mining_result = TextMiningResult.objects.create(
                dataset_name=dataset_name,
                clustering_result=json.dumps(clustering_result),
                wordcloud_plots=json.dumps({
                    'tsne_image': tsne_image,
                    'wordclouds': wordcloud_results
                })
            )
            
            # 生成摘要
            summary = {
                'total_texts': len(texts),
                'n_clusters': clustering_result['n_clusters'],
                'clustering_method': clustering_method,
                'data_source': 'uploaded_dataset'
            }
            
            return {
                'result_id': mining_result.id,
                'summary': summary,
                'clustering': clustering_result,
                'tsne_image': tsne_image,
                'wordclouds': wordcloud_results
            }
            
        except Exception as e:
            print(f"文本挖掘分析错误: {e}")
            raise

def main():
    """主函数 - 用于测试"""
    analyzer = TextMiningAnalyzer()
    
    try:
        result = analyzer.run_complete_analysis(
            dataset_name="医疗问答数据集分析",
            clustering_method='kmeans',
            n_clusters=6
        )
        
        print("=== 分析结果摘要 ===")
        print(f"总文本数: {result['summary']['total_texts']}")
        print(f"聚类数: {result['summary']['n_clusters']}")
        print(f"聚类方法: {result['summary']['clustering_method']}")
        print(f"生成了 {len(result['wordclouds'])} 个词云图")
        
    except Exception as e:
        print(f"分析失败: {e}")

if __name__ == "__main__":
    main() 