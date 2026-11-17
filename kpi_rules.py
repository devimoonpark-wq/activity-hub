"""Rules describe how KPI values may be summarized. Never sum snapshots or ratings."""
KPI_RULES = {
    'Belajar Digital': {
        'Average CTR (GSC)': 'source_required', 'Average Position (GSC)': 'source_required',
        'Confirmed Participant Batch 2': 'batch', 'Course Regis Batch 2': 'batch',
        'Impressions (GSC)': 'sum', 'Indexed pages': 'latest', 'Organic Clicks (GSC)': 'sum',
        'Potential to hire Batch 2': 'batch', 'Total Published Article': 'latest'},
    'Career Page': {
        'Average CTR (GSC)': 'source_required', 'Average Position (GSC)': 'source_required',
        'Impressions (GSC)': 'sum', 'Indexed pages': 'latest', 'Organic Clicks (GSC)': 'sum',
        'Total Published Article': 'latest'},
    'Employee Engagement': {'Activity participants': 'event', 'Review from participants': 'event'},
    'Employer Branding': {'Glassdoor rating': 'latest', 'Glassdoor review': 'latest'},
    'Social Media': {
        'BD Linkedin Engagements': 'sum', 'BD Linkedin Followers': 'latest',
        'BD Linkedin Impressions': 'sum', 'LPM Instagram Followers': 'latest',
        'LPM Linkedin Engagements': 'sum', 'LPM Linkedin Followers': 'latest',
        'LPM Linkedin Impressions': 'sum', 'Published BD Linkedin Post': 'sum',
        'Published Linkedin Post': 'sum', 'Published xlWin Linkedin Post': 'sum',
        'xlWin Linkedin Engagements': 'sum', 'xlWin Linkedin Followers': 'latest',
        'xlWin Linkedin Impressions': 'sum'},
    'University Partnership': {'Event participants': 'event'},
}

def get_kpi_rule(category, metric):
    return KPI_RULES.get(category, {}).get(metric, 'unclassified')
