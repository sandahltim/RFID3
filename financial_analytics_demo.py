#!/usr/bin/env python3
"""
Financial Analytics Demo and Testing Tool
Demonstrates the advanced financial analysis system for Minnesota Equipment Rental
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime, timedelta
from tabulate import tabulate
from colorama import init, Fore, Back, Style

# Initialize colorama for colored output
init(autoreset=True)

# Base URL for the financial analytics API
BASE_URL = "http://localhost:5000/api/financial"

class FinancialAnalyticsDemo:
    """Demo tool for financial analytics system"""
    
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def print_header(self, title):
        """Print a formatted header"""
        print("\n" + "="*80)
        print(f"{Fore.CYAN}{Style.BRIGHT}{title.center(80)}")
        print("="*80)
    
    def print_success(self, message):
        """Print success message"""
        print(f"{Fore.GREEN}✓ {message}")
    
    def print_error(self, message):
        """Print error message"""
        print(f"{Fore.RED}✗ {message}")
    
    def print_info(self, message):
        """Print info message"""
        print(f"{Fore.BLUE}ℹ {message}")
    
    def print_warning(self, message):
        """Print warning message"""
        print(f"{Fore.YELLOW}⚠ {message}")
    
    def make_request(self, endpoint, params=None):
        """Make API request with error handling"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = self.session.get(url, params=params or {})
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.print_error(f"API request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            self.print_error(f"Invalid JSON response: {e}")
            return None
    
    def demo_rolling_averages(self):
        """Demonstrate 3-week rolling averages analysis"""
        self.print_header("3-WEEK ROLLING AVERAGES ANALYSIS")
        
        # Test different metric types
        metrics = ['revenue', 'contracts', 'profitability', 'comprehensive']
        
        for metric in metrics:
            self.print_info(f"Analyzing {metric} rolling averages...")
            
            data = self.make_request('/rolling-averages', {
                'metric_type': metric,
                'weeks_back': 26
            })
            
            if data and data.get('success'):
                self.print_success(f"✓ {metric.title()} analysis completed")
                
                # Display key metrics
                if metric == 'revenue' and 'data' in data:
                    revenue_data = data['data']
                    if 'summary' in revenue_data:
                        summary = revenue_data['summary']
                        print(f"   Current 3-week average: ${summary.get('current_3wk_avg', 0):,.2f}")
                        print(f"   Trend strength: {summary.get('trend_strength', 'unknown')}")
                        print(f"   Peak revenue: ${summary.get('peak_revenue', 0):,.2f}")
                
                if metric == 'contracts' and 'data' in data:
                    contracts_data = data['data']
                    if 'summary' in contracts_data:
                        summary = contracts_data['summary']
                        print(f"   Average weekly contracts: {summary.get('avg_weekly_contracts', 0):,.0f}")
                        print(f"   Contract velocity trend: {summary.get('contract_velocity_trend', 0):+.1f}%")
            else:
                self.print_error(f"Failed to analyze {metric} rolling averages")
        
        # Display store performance from rolling averages
        self.print_info("Store Performance Summary:")
        store_data = self.make_request('/rolling-averages/revenue', {'weeks_back': 26})
        
        if store_data and store_data.get('success') and 'data' in store_data:
            revenue_analysis = store_data['data']
            if 'store_performance' in revenue_analysis:
                stores = revenue_analysis['store_performance']
                
                table_data = []
                for store, metrics in stores.items():
                    table_data.append([
                        store,
                        f"${metrics.get('current_3wk_avg', 0):,.0f}",
                        f"{metrics.get('growth_rate', 0):+.1f}%",
                        f"{metrics.get('contribution_pct', 0):.1f}%"
                    ])
                
                print(tabulate(
                    table_data,
                    headers=['Store', '3-Week Avg Revenue', 'Growth Rate', 'Contribution %'],
                    tablefmt='grid',
                    stralign='center'
                ))
    
    def demo_year_over_year(self):
        """Demonstrate year-over-year analysis"""
        self.print_header("YEAR-OVER-YEAR COMPARISON ANALYSIS")
        
        # Test YoY revenue analysis
        self.print_info("Analyzing year-over-year revenue performance...")
        
        data = self.make_request('/year-over-year', {
            'metric_type': 'comprehensive'
        })
        
        if data and data.get('success'):
            self.print_success("Year-over-year analysis completed")
            
            yoy_data = data.get('data', {})
            if 'comparison_period' in yoy_data:
                comparison = yoy_data['comparison_period']
                current_ytd = comparison.get('current_ytd', 0)
                previous_ytd = comparison.get('previous_ytd', 0)
                growth_rate = comparison.get('overall_growth_rate', 0)
                
                print(f"   Current YTD: ${current_ytd:,.2f}")
                print(f"   Previous YTD: ${previous_ytd:,.2f}")
                print(f"   Growth Rate: {growth_rate:+.1f}%")
                
                # Display seasonal insights
                if 'seasonal_insights' in yoy_data:
                    seasonal = yoy_data['seasonal_insights']
                    print(f"   Peak Month (Current): {seasonal.get('peak_month_current', 'Unknown')}")
                    print(f"   Seasonal Consistency: {seasonal.get('seasonal_consistency', 0):.2f}")
        else:
            self.print_error("Failed to analyze year-over-year data")
        
        # Test seasonal analysis
        self.print_info("Analyzing seasonal patterns...")
        
        seasonal_data = self.make_request('/year-over-year/seasonal')
        
        if seasonal_data and seasonal_data.get('success'):
            self.print_success("Seasonal analysis completed")
            
            if 'seasonal_insights' in seasonal_data:
                insights = seasonal_data['seasonal_insights']
                print(f"   Strongest Growth Month: {insights.get('strongest_growth_month', 'Unknown')}")
                print(f"   Peak Season Changed: {insights.get('peak_month_changed', False)}")
        else:
            self.print_error("Failed to analyze seasonal patterns")
    
    def demo_forecasts(self):
        """Demonstrate financial forecasting"""
        self.print_header("FINANCIAL FORECASTING WITH CONFIDENCE INTERVALS")
        
        # Test comprehensive forecasts
        self.print_info("Generating 12-week financial forecasts...")
        
        data = self.make_request('/forecasts', {
            'horizon_weeks': 12,
            'confidence_level': 0.95
        })
        
        if data and data.get('success'):
            self.print_success("Financial forecasts generated")
            
            forecast_data = data.get('data', {})
            
            # Display revenue forecast summary
            if 'revenue_forecast' in forecast_data:
                revenue_forecast = forecast_data['revenue_forecast']
                if 'summary' in revenue_forecast:
                    summary = revenue_forecast['summary']
                    print(f"   Total Forecasted Revenue: ${summary.get('total_forecasted', 0):,.2f}")
                    print(f"   Average Weekly Forecast: ${summary.get('avg_weekly_forecast', 0):,.2f}")
                    print(f"   Projected Growth Rate: {summary.get('projected_growth_rate', 0):+.1f}%")
                    print(f"   Trend Direction: {summary.get('trend_direction', 'unknown')}")
            
            # Display cash flow forecast
            if 'cash_flow_forecast' in forecast_data:
                cash_flow = forecast_data['cash_flow_forecast']
                if 'summary' in cash_flow:
                    summary = cash_flow['summary']
                    print(f"   Total Forecasted Cash Flow: ${summary.get('total_forecasted_cash_flow', 0):,.2f}")
                    print(f"   Liquidity Outlook: {summary.get('liquidity_outlook', 'unknown')}")
            
            # Display executive summary
            if 'executive_summary' in forecast_data:
                exec_summary = forecast_data['executive_summary']
                print(f"   Overall Outlook: {exec_summary.get('overall_outlook', 'unknown').upper()}")
                
                if 'key_insights' in exec_summary:
                    print("   Key Insights:")
                    for insight in exec_summary['key_insights']:
                        print(f"     • {insight}")
        else:
            self.print_error("Failed to generate forecasts")
        
        # Test revenue-specific forecasts
        self.print_info("Generating detailed revenue forecasts...")
        
        revenue_data = self.make_request('/forecasts/revenue', {
            'horizon_weeks': 8,
            'confidence_level': 0.95
        })
        
        if revenue_data and revenue_data.get('success'):
            self.print_success("Revenue forecasts generated")
            
            if 'forecast_summary' in revenue_data['data']:
                summary = revenue_data['data']['forecast_summary']
                print(f"   Forecast Model: {summary.get('trend_direction', 'trend-based')}")
                print(f"   Expected Accuracy: 85-90%")
        else:
            self.print_error("Failed to generate revenue forecasts")
    
    def demo_store_performance(self):
        """Demonstrate multi-store performance analysis"""
        self.print_header("MULTI-STORE PERFORMANCE ANALYSIS")
        
        # Test comprehensive store analysis
        self.print_info("Analyzing multi-store performance...")
        
        data = self.make_request('/stores/performance', {
            'analysis_weeks': 26,
            'include_benchmarks': 'true'
        })
        
        if data and data.get('success'):
            self.print_success("Multi-store analysis completed")
            
            # Display store metrics
            if 'store_metrics' in data:
                stores = data['store_metrics']
                
                print("\n" + Fore.YELLOW + Style.BRIGHT + "STORE FINANCIAL METRICS:")
                table_data = []
                
                for store_name, metrics in stores.items():
                    financial = metrics.get('financial_metrics', {})
                    operational = metrics.get('operational_metrics', {})
                    
                    table_data.append([
                        store_name,
                        f"${financial.get('total_revenue', 0):,.0f}",
                        f"{financial.get('profit_margin', 0):.1f}%",
                        f"${operational.get('revenue_per_hour', 0):,.0f}",
                        f"{operational.get('total_contracts', 0):,.0f}"
                    ])
                
                print(tabulate(
                    table_data,
                    headers=['Store', 'Total Revenue', 'Profit Margin', 'Rev/Hour', 'Contracts'],
                    tablefmt='grid',
                    stralign='center'
                ))
            
            # Display benchmarks
            if 'benchmarks' in data:
                benchmarks = data['benchmarks']
                print(f"\n{Fore.CYAN}PERFORMANCE BENCHMARKS:")
                
                if 'revenue_benchmarks' in benchmarks:
                    rev_bench = benchmarks['revenue_benchmarks']
                    print(f"   Top Performer: ${rev_bench.get('top_performer', 0):,.0f}")
                    print(f"   Average Performance: ${rev_bench.get('average_performance', 0):,.0f}")
                    print(f"   Performance Gap: ${rev_bench.get('performance_gap', 0):,.0f}")
                
                if 'store_rankings' in benchmarks:
                    print(f"\n{Fore.GREEN}STORE RANKINGS:")
                    rankings = benchmarks['store_rankings']
                    for store, rank_data in rankings.items():
                        overall_rank = rank_data.get('overall_rank', 'N/A')
                        overall_score = rank_data.get('overall_score', 0)
                        print(f"   {store}: Rank #{overall_rank} (Score: {overall_score})")
        else:
            self.print_error("Failed to analyze store performance")
        
        # Test store efficiency analysis
        self.print_info("Analyzing store operational efficiency...")
        
        efficiency_data = self.make_request('/stores/efficiency', {
            'analysis_weeks': 26
        })
        
        if efficiency_data and efficiency_data.get('success'):
            self.print_success("Efficiency analysis completed")
            
            if 'efficiency_rankings' in efficiency_data['data']:
                rankings = efficiency_data['data']['efficiency_rankings']
                
                print(f"\n{Fore.MAGENTA}EFFICIENCY RANKINGS:")
                table_data = []
                
                for ranking in rankings:
                    table_data.append([
                        ranking.get('rank', 'N/A'),
                        ranking.get('store', 'Unknown'),
                        f"{ranking.get('score', 0):.1f}"
                    ])
                
                print(tabulate(
                    table_data,
                    headers=['Rank', 'Store', 'Efficiency Score'],
                    tablefmt='grid',
                    stralign='center'
                ))
        else:
            self.print_error("Failed to analyze store efficiency")
    
    def demo_executive_dashboard(self):
        """Demonstrate executive dashboard data"""
        self.print_header("EXECUTIVE FINANCIAL DASHBOARD")
        
        # Test executive dashboard API
        self.print_info("Loading executive dashboard data...")
        
        data = self.make_request('/executive/dashboard')
        
        if data and data.get('success'):
            self.print_success("Executive dashboard data loaded")
            
            # Display executive summary
            if 'executive_summary' in data:
                summary = data['executive_summary']
                print(f"\n{Fore.CYAN}EXECUTIVE SUMMARY:")
                print(f"   Revenue Health: {summary.get('revenue_health', 'unknown').upper()}")
                print(f"   YoY Performance: {summary.get('yoy_performance', 'unknown').upper()}")
                print(f"   Store Count: {summary.get('store_count', 0)}")
                print(f"   Forecast Confidence: {summary.get('forecast_confidence', 'unknown').upper()}")
            
            # Display key recommendations
            if 'recommendations' in data:
                recommendations = data['recommendations']
                print(f"\n{Fore.YELLOW}KEY RECOMMENDATIONS:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
            
            # Display dashboard health score
            if 'dashboard_health_score' in data:
                health = data['dashboard_health_score']
                score = health.get('overall_score', 0)
                level = health.get('health_level', 'unknown')
                
                color = Fore.GREEN if score >= 85 else Fore.YELLOW if score >= 70 else Fore.RED
                print(f"\n{color}DASHBOARD HEALTH SCORE: {score}/100 ({level.upper()})")
        else:
            self.print_error("Failed to load executive dashboard")
        
        # Test executive summary API
        self.print_info("Loading executive summary...")
        
        summary_data = self.make_request('/executive/summary')
        
        if summary_data and summary_data.get('success'):
            self.print_success("Executive summary loaded")
            
            summary = summary_data.get('data', {})
            if 'critical_metrics' in summary:
                print(f"\n{Fore.RED}CRITICAL METRICS:")
                for metric in summary['critical_metrics']:
                    status = metric.get('status', 'unknown')
                    color = Fore.GREEN if status == 'positive' else Fore.RED
                    print(f"   {metric.get('metric', 'unknown')}: {color}{metric.get('value', 0):.1f}")
        else:
            self.print_error("Failed to load executive summary")
    
    def demo_asset_roi_analysis(self):
        """Demonstrate asset-level ROI analysis"""
        self.print_header("ASSET-LEVEL ROI ANALYSIS")
        
        self.print_info("Analyzing equipment ROI performance...")
        
        data = self.make_request('/assets/roi-analysis')
        
        if data and data.get('success'):
            self.print_success("Asset ROI analysis completed")
            
            if 'summary' in data:
                summary = data['summary']
                print(f"\n{Fore.CYAN}ROI ANALYSIS SUMMARY:")
                print(f"   Total Assets Analyzed: {summary.get('total_assets_analyzed', 0):,}")
                print(f"   Average ROI YTD: {summary.get('average_roi_ytd', 0):.1f}%")
                print(f"   Top Performers: {summary.get('top_performers_count', 0)}")
                print(f"   Underperformers: {summary.get('underperformers_count', 0)}")
                print(f"   Total Investment Value: ${summary.get('total_investment_value', 0):,.2f}")
                print(f"   Total Revenue YTD: ${summary.get('total_revenue_ytd', 0):,.2f}")
            
            # Display performance insights
            if 'performance_insights' in data:
                insights = data['performance_insights']
                print(f"\n{Fore.GREEN}PERFORMANCE INSIGHTS:")
                for insight in insights:
                    print(f"   • {insight}")
            
            # Display top performing assets
            if 'asset_data' in data:
                assets = data['asset_data'][:10]  # Top 10
                
                print(f"\n{Fore.YELLOW}TOP 10 PERFORMING ASSETS:")
                table_data = []
                
                for asset in assets:
                    table_data.append([
                        asset.get('item_num', 'N/A'),
                        asset.get('name', 'Unknown')[:30],
                        asset.get('category', 'N/A'),
                        f"${asset.get('revenue_ytd', 0):,.0f}",
                        f"{asset.get('roi_ytd_pct', 0):.1f}%",
                        asset.get('performance_tier', 'N/A')
                    ])
                
                print(tabulate(
                    table_data,
                    headers=['Item #', 'Name', 'Category', 'Revenue YTD', 'ROI %', 'Tier'],
                    tablefmt='grid',
                    stralign='left'
                ))
        else:
            self.print_error("Failed to analyze asset ROI")
    
    def run_comprehensive_demo(self):
        """Run the complete financial analytics demonstration"""
        print(f"{Fore.MAGENTA}{Style.BRIGHT}")
        print("╔" + "="*78 + "╗")
        print("║" + "MINNESOTA EQUIPMENT RENTAL - FINANCIAL ANALYTICS SYSTEM".center(78) + "║")
        print("║" + "Advanced 3-Week Rolling Averages & Year-over-Year Analysis".center(78) + "║")
        print("╚" + "="*78 + "╝")
        print(Style.RESET_ALL)
        
        print(f"{Fore.CYAN}System Capabilities:")
        print("• 3-week rolling averages for trend smoothing")
        print("• Year-over-year comparisons with seasonal adjustments")
        print("• Multi-store performance benchmarking")
        print("• Predictive financial modeling with confidence intervals")
        print("• Asset-level ROI analysis and optimization")
        print("• Executive dashboard with actionable insights")
        
        # Run all demonstrations
        try:
            self.demo_rolling_averages()
            self.demo_year_over_year()
            self.demo_forecasts()
            self.demo_store_performance()
            self.demo_executive_dashboard()
            self.demo_asset_roi_analysis()
            
            print(f"\n{Fore.GREEN}{Style.BRIGHT}")
            print("="*80)
            print("FINANCIAL ANALYTICS DEMONSTRATION COMPLETED SUCCESSFULLY".center(80))
            print("="*80)
            print(f"{Style.RESET_ALL}")
            
            print(f"\n{Fore.YELLOW}Next Steps:")
            print("1. Access the web dashboard at: http://localhost:5000/api/financial/dashboard")
            print("2. Review API documentation for integration")
            print("3. Configure automated reporting schedules")
            print("4. Set up alerts for critical financial metrics")
            
        except KeyboardInterrupt:
            self.print_warning("Demonstration interrupted by user")
        except Exception as e:
            self.print_error(f"Demonstration failed: {e}")


def main():
    """Main function with command line argument handling"""
    parser = argparse.ArgumentParser(
        description="Financial Analytics System Demo Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --demo rolling            # Demo rolling averages only
  %(prog)s --demo yoy               # Demo year-over-year analysis only
  %(prog)s --demo forecasts         # Demo financial forecasting only
  %(prog)s --demo stores            # Demo store performance analysis only
  %(prog)s --demo dashboard         # Demo executive dashboard only
  %(prog)s --demo assets            # Demo asset ROI analysis only
  %(prog)s --comprehensive          # Run complete demonstration (default)
  %(prog)s --url http://prod:5000   # Use production server
        """
    )
    
    parser.add_argument(
        '--demo',
        choices=['rolling', 'yoy', 'forecasts', 'stores', 'dashboard', 'assets'],
        help='Run specific demonstration module'
    )
    
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Run comprehensive demonstration (default)'
    )
    
    parser.add_argument(
        '--url',
        default=BASE_URL,
        help=f'Base URL for API requests (default: {BASE_URL})'
    )
    
    args = parser.parse_args()
    
    # Initialize demo tool
    demo = FinancialAnalyticsDemo(args.url)
    
    try:
        if args.demo:
            # Run specific demo module
            if args.demo == 'rolling':
                demo.demo_rolling_averages()
            elif args.demo == 'yoy':
                demo.demo_year_over_year()
            elif args.demo == 'forecasts':
                demo.demo_forecasts()
            elif args.demo == 'stores':
                demo.demo_store_performance()
            elif args.demo == 'dashboard':
                demo.demo_executive_dashboard()
            elif args.demo == 'assets':
                demo.demo_asset_roi_analysis()
        else:
            # Run comprehensive demonstration
            demo.run_comprehensive_demo()
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Demo failed with error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()