"""
모니터링 대시보드
Streamlit 기반 실시간 성능 지표 시각화
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json


class MetricsCollector:
    """성능 지표 수집기"""
    
    def __init__(self):
        self.metrics = {
            'uploads': [],
            'optimizations': [],
            'cdn_requests': [],
            'errors': []
        }
    
    def record_upload(self, file_size: int, duration_sec: float, success: bool):
        """업로드 기록"""
        self.metrics['uploads'].append({
            'timestamp': datetime.now().isoformat(),
            'file_size_mb': file_size / (1024 * 1024),
            'duration_sec': duration_sec,
            'success': success,
            'throughput_mbps': (file_size / (1024 * 1024)) / duration_sec if duration_sec > 0 else 0
        })
    
    def record_optimization(self, original_size: int, optimized_size: int, 
                           reduction_percent: float, duration_sec: float):
        """최적화 기록"""
        self.metrics['optimizations'].append({
            'timestamp': datetime.now().isoformat(),
            'original_size_mb': original_size / (1024 * 1024),
            'optimized_size_mb': optimized_size / (1024 * 1024),
            'reduction_percent': reduction_percent,
            'duration_sec': duration_sec
        })
    
    def record_cdn_request(self, response_time_ms: int, cache_status: str, 
                          status_code: int):
        """CDN 요청 기록"""
        self.metrics['cdn_requests'].append({
            'timestamp': datetime.now().isoformat(),
            'response_time_ms': response_time_ms,
            'cache_status': cache_status,
            'status_code': status_code,
            'is_cache_hit': cache_status == 'HIT'
        })
    
    def record_error(self, error_type: str, message: str, component: str):
        """에러 기록"""
        self.metrics['errors'].append({
            'timestamp': datetime.now().isoformat(),
            'type': error_type,
            'message': message,
            'component': component
        })
    
    def get_summary_stats(self) -> dict:
        """요약 통계"""
        uploads_df = pd.DataFrame(self.metrics['uploads'])
        optimizations_df = pd.DataFrame(self.metrics['optimizations'])
        cdn_df = pd.DataFrame(self.metrics['cdn_requests'])
        
        stats = {
            'total_uploads': len(uploads_df),
            'upload_success_rate': (uploads_df['success'].sum() / len(uploads_df) * 100) if len(uploads_df) > 0 else 0,
            'avg_upload_speed_mbps': uploads_df['throughput_mbps'].mean() if len(uploads_df) > 0 else 0,
            'total_optimizations': len(optimizations_df),
            'avg_reduction_percent': optimizations_df['reduction_percent'].mean() if len(optimizations_df) > 0 else 0,
            'total_storage_saved_mb': (optimizations_df['original_size_mb'].sum() - optimizations_df['optimized_size_mb'].sum()) if len(optimizations_df) > 0 else 0,
            'total_cdn_requests': len(cdn_df),
            'cdn_cache_hit_rate': (cdn_df['is_cache_hit'].sum() / len(cdn_df) * 100) if len(cdn_df) > 0 else 0,
            'avg_response_time_ms': cdn_df['response_time_ms'].mean() if len(cdn_df) > 0 else 0,
            'total_errors': len(self.metrics['errors'])
        }
        
        return stats
    
    def export_to_json(self, filepath: str):
        """JSON 형식으로 내보내기"""
        with open(filepath, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def import_from_json(self, filepath: str):
        """JSON에서 가져오기"""
        with open(filepath, 'r') as f:
            self.metrics = json.load(f)


def create_dashboard():
    """Streamlit 대시보드 생성"""
    
    st.set_page_config(
        page_title="NCP Object Storage Pipeline Monitor",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("🚀 NCP Object Storage 통합 파이프라인 모니터링")
    st.markdown("**Object Storage → Image Optimizer → CDN+ 실시간 성능 지표**")
    
    # 샘플 데이터 생성 (실제로는 MetricsCollector에서 로드)
    collector = MetricsCollector()
    
    # Mock 데이터
    import random
    for i in range(50):
        collector.record_upload(
            file_size=random.randint(500000, 5000000),
            duration_sec=random.uniform(0.5, 3.0),
            success=random.random() > 0.05
        )
        collector.record_optimization(
            original_size=random.randint(1000000, 10000000),
            optimized_size=random.randint(300000, 3000000),
            reduction_percent=random.uniform(60, 85),
            duration_sec=random.uniform(0.3, 2.0)
        )
        collector.record_cdn_request(
            response_time_ms=random.randint(20, 200),
            cache_status=random.choice(['HIT', 'HIT', 'HIT', 'MISS']),
            status_code=200
        )
    
    stats = collector.get_summary_stats()
    
    # KPI 카드
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "업로드 성공률",
            f"{stats['upload_success_rate']:.1f}%",
            delta="목표: 99.0%",
            delta_color="normal" if stats['upload_success_rate'] >= 99 else "inverse"
        )
    
    with col2:
        st.metric(
            "평균 파일 크기 감소",
            f"{stats['avg_reduction_percent']:.1f}%",
            delta="목표: 60%",
            delta_color="normal" if stats['avg_reduction_percent'] >= 60 else "inverse"
        )
    
    with col3:
        st.metric(
            "CDN 캐시 히트율",
            f"{stats['cdn_cache_hit_rate']:.1f}%",
            delta="목표: 80%",
            delta_color="normal" if stats['cdn_cache_hit_rate'] >= 80 else "inverse"
        )
    
    with col4:
        st.metric(
            "평균 응답 시간",
            f"{stats['avg_response_time_ms']:.0f}ms",
            delta="목표: <500ms",
            delta_color="inverse" if stats['avg_response_time_ms'] < 500 else "normal"
        )
    
    st.divider()
    
    # 차트 섹션
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 업로드 성능", 
        "🖼️ 이미지 최적화", 
        "🌐 CDN 성능", 
        "💰 비용 분석"
    ])
    
    with tab1:
        st.subheader("업로드 성능 분석")
        
        uploads_df = pd.DataFrame(collector.metrics['uploads'])
        
        if not uploads_df.empty:
            # 업로드 속도 추이
            fig_upload = px.line(
                uploads_df,
                y='throughput_mbps',
                title='업로드 속도 추이 (MB/s)',
                labels={'throughput_mbps': '속도 (MB/s)', 'index': '요청 번호'}
            )
            fig_upload.update_traces(
                line_color='#FF6B6B',  # 선명한 빨강
                line_width=3
            )
            fig_upload.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_upload, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 파일 크기 분포
                fig_size = px.histogram(
                    uploads_df,
                    x='file_size_mb',
                    nbins=20,
                    title='파일 크기 분포',
                    color_discrete_sequence=['#4A90E2']  # 진한 파란색
                )
                fig_size.update_layout(
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig_size, use_container_width=True)
            
            with col2:
                # 성공/실패 비율
                success_counts = uploads_df['success'].value_counts()
                fig_success = px.pie(
                    values=success_counts.values,
                    names=['성공' if k else '실패' for k in success_counts.index],
                    title='업로드 성공/실패',
                    color_discrete_sequence=['#51CF66', '#FF6B6B']  # 초록, 빨강
                )
                fig_success.update_traces(
                    textposition='inside',
                    textinfo='percent+label',
                    marker=dict(line=dict(color='white', width=2))
                )
                st.plotly_chart(fig_success, use_container_width=True)
    
    with tab2:
        st.subheader("이미지 최적화 효과")
        
        opt_df = pd.DataFrame(collector.metrics['optimizations'])
        
        if not opt_df.empty:
            # 압축률 추이
            fig_reduction = px.line(
                opt_df,
                y='reduction_percent',
                title='파일 크기 감소율 추이 (%)',
                labels={'reduction_percent': '감소율 (%)', 'index': '처리 번호'}
            )
            fig_reduction.update_traces(
                line_color='#845EC2',  # 보라색
                line_width=3
            )
            fig_reduction.add_hline(
                y=60, 
                line_dash="dash", 
                line_color="#FF6B6B",  # 빨강 점선
                line_width=2,
                annotation_text="목표: 60%"
            )
            fig_reduction.update_layout(
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            st.plotly_chart(fig_reduction, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 최적화 전후 비교
                total_original = opt_df['original_size_mb'].sum()
                total_optimized = opt_df['optimized_size_mb'].sum()
                
                fig_comparison = go.Figure(data=[
                    go.Bar(
                        name='최적화 전', 
                        x=['Total'], 
                        y=[total_original],
                        marker_color='#FF8787'  # 연한 빨강
                    ),
                    go.Bar(
                        name='최적화 후', 
                        x=['Total'], 
                        y=[total_optimized],
                        marker_color='#51CF66'  # 초록
                    )
                ])
                fig_comparison.update_layout(
                    title='전체 저장 용량 비교 (MB)',
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                st.success(f"💾 총 {total_original - total_optimized:.2f}MB 절감!")
            
            with col2:
                # 최적화 속도
                fig_speed = px.histogram(
                    opt_df,
                    x='duration_sec',
                    nbins=15,
                    title='최적화 소요 시간 분포 (초)'
                )
                st.plotly_chart(fig_speed, use_container_width=True)
    
    with tab3:
        st.subheader("CDN 성능 모니터링")
        
        cdn_df = pd.DataFrame(collector.metrics['cdn_requests'])
        
        if not cdn_df.empty:
            # 응답 시간 추이
            fig_response = px.line(
                cdn_df,
                y='response_time_ms',
                title='CDN 응답 시간 추이 (ms)',
                labels={'response_time_ms': '응답 시간 (ms)', 'index': '요청 번호'}
            )
            fig_response.add_hline(y=500, line_dash="dash", line_color="red",
                                  annotation_text="SLA: 500ms")
            st.plotly_chart(fig_response, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 캐시 상태 분포
                cache_counts = cdn_df['cache_status'].value_counts()
                fig_cache = px.pie(
                    values=cache_counts.values,
                    names=cache_counts.index,
                    title='캐시 HIT/MISS 분포'
                )
                st.plotly_chart(fig_cache, use_container_width=True)
            
            with col2:
                # 캐시별 응답 시간
                fig_cache_perf = px.box(
                    cdn_df,
                    x='cache_status',
                    y='response_time_ms',
                    title='캐시 상태별 응답 시간'
                )
                st.plotly_chart(fig_cache_perf, use_container_width=True)
    
    with tab4:
        st.subheader("비용 효율성 분석")
        
        # 비용 계산 (예시)
        storage_cost_per_gb = 0.024  # NCP Object Storage 가격 (USD/GB/month)
        cdn_cost_per_gb = 0.08  # CDN 트래픽 가격 (USD/GB)
        
        total_storage_mb = stats['total_storage_saved_mb']
        total_storage_gb = total_storage_mb / 1024
        
        monthly_savings = total_storage_gb * storage_cost_per_gb
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "최적화로 절감된 스토리지",
                f"{total_storage_gb:.2f} GB"
            )
        
        with col2:
            st.metric(
                "월간 예상 비용 절감",
                f"${monthly_savings:.2f}"
            )
        
        with col3:
            st.metric(
                "연간 예상 비용 절감",
                f"${monthly_savings * 12:.2f}"
            )
        
        st.info("""
        💡 **비용 절감 팁**
        - 이미지 최적화로 스토리지 비용 40% 절감
        - CDN 캐시 히트율 향상으로 Origin 트래픽 비용 감소
        - WebP 포맷 사용으로 대역폭 비용 최소화
        """)
    
    # 푸터
    st.divider()
    st.caption(f"마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    st.caption("📊 NCP Object Storage 통합 파이프라인 모니터링 v1.0 | Phase 2 Enhanced")


if __name__ == '__main__':
    create_dashboard()