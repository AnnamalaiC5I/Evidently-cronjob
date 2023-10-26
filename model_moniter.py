import datetime
from sklearn import datasets
import pandas as pd
import evidently
from evidently.metrics import ColumnDriftMetric
from evidently.metrics import ColumnSummaryMetric
from evidently.metrics import DatasetDriftMetric
from evidently.metrics import DatasetMissingValuesMetric
from evidently.report import Report
from evidently.test_preset import DataDriftTestPreset
from evidently.test_suite import TestSuite
from evidently.ui.dashboards import CounterAgg
from evidently.ui.dashboards import DashboardPanelCounter
from evidently.ui.dashboards import DashboardPanelPlot
from evidently.ui.dashboards import PanelValue
from evidently.ui.dashboards import PlotType
from evidently.ui.dashboards import ReportFilter
from evidently.ui.remote import RemoteWorkspace
from evidently.ui.workspace import Workspace
from evidently.ui.workspace import WorkspaceBase
import os
import numpy as np
import psycopg2


conn = psycopg2.connect(host='mydb.czj96lm1eush.us-west-2.rds.amazonaws.com', dbname='postgres',
                        user='postgres', password='Admin123*')
cursor = conn.cursor()


postgres_insert_query = """ INSERT INTO usecase1 (label,General_Health,Checkup,Age_Category,Height,Weight,BMI,Alcohol_Consumption,Fruit_Consumption,Green_Vegetables_Consumption,FriedPotato_Consumption,Exercise_Yes,Skin_Cancer_Yes,Other_Cancer_Yes,Depression_Yes,Diabetes_No_pre_diabetes_or_borderline_diabetes,Diabetes_Yes,Diabetes_Yes_but_female_told_only_during_pregnancy,Arthritis_Yes,Sex_Male,Smoking_History_Yes,PATIENT_ID,predictions) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
 

column_names = ['label','General_Health', 'Checkup', 'Age_Category', 'Height', 'Weight', 'BMI',
       'Alcohol_Consumption', 'Fruit_Consumption',
       'Green_Vegetables_Consumption', 'FriedPotato_Consumption',
       'Exercise_Yes', 'Skin_Cancer_Yes', 'Other_Cancer_Yes', 'Depression_Yes',
       'Diabetes_No_pre-diabetes_or_borderline_diabetes', 'Diabetes_Yes',
       'Diabetes_Yes_but_female_told_only_during_pregnancy', 'Arthritis_Yes',
       'Sex_Male', 'Smoking_History_Yes', 'PATIENT_ID','predictions']

command1 =   """ SELECT * FROM usecase1; """
cursor.execute(command1)
rows = cursor.fetchall()
dfs= rows.copy()
curr_data = pd.DataFrame(dfs, columns=column_names)


command2 =   """SELECT * FROM usecase1 WHERE label = 'train'; """
cursor.execute(command2)
rows = cursor.fetchall()
ref_data = rows.copy()
ref_data = pd.DataFrame(ref_data, columns=column_names)



def create_project(workspace: WorkspaceBase):
    project = workspace.create_project(YOUR_PROJECT_NAME)
    project.description = YOUR_PROJECT_DESCRIPTION
    project.dashboard.add_panel(
        DashboardPanelCounter(
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            agg=CounterAgg.NONE,
            title="Pharma Dataset",
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Data Entries",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="DatasetMissingValuesMetric",
                field_path=DatasetMissingValuesMetric.fields.current.number_of_rows,
                legend="count",
            ),
            text="count",
            agg=CounterAgg.SUM,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelCounter(
            title="Share of Drifted Features",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            value=PanelValue(
                metric_id="DatasetDriftMetric",
                field_path="share_of_drifted_columns",
                legend="share",
            ),
            text="share",
            agg=CounterAgg.LAST,
            size=1,
        )
    )
    project.dashboard.add_panel(
        DashboardPanelPlot(
            title="Dataset Quality",
            filter=ReportFilter(metadata_values={}, tag_values=[]),
            values=[
                PanelValue(metric_id="DatasetDriftMetric", field_path="share_of_drifted_columns", legend="Drift Share"),
                PanelValue(
                    metric_id="DatasetMissingValuesMetric",
                    field_path=DatasetMissingValuesMetric.fields.current.share_of_missing_values,
                    legend="Missing Values Share",
                ),
            ],
            plot_type=PlotType.LINE,
        )
    )

    project.save()
    return project

def create_report(i: int):
    data_drift_report = Report(
        metrics=[
            evidently.metric_preset.DataDriftPreset(),
            DatasetMissingValuesMetric(),
            ColumnSummaryMetric('predictions'),
        ],
        timestamp=datetime.datetime.now() + datetime.timedelta(days=i),
    )

    data_drift_report.run(reference_data=ref_data, current_data=curr_data)
    return data_drift_report

def create_test_suite(i: int):
    data_drift_test_suite = TestSuite(
        tests=[DataDriftTestPreset()],
        timestamp=datetime.datetime.now() + datetime.timedelta(days=i),
    )

    data_drift_test_suite.run(reference_data=ref_data, current_data=curr_data)
    return data_drift_test_suite

def create_demo_project(ws, workspace, exist):
    
    if exist:
        print("if executed")
        project_id = exist[0].id
        
    else:
        
        project = create_project(ws)
        project_id = project.id

    
    
    report = create_report(i=1)
    ws.add_report(project_id, report)

    test_suite = create_test_suite(i=1)
    ws.add_test_suite(project_id, test_suite)
    


WORKSPACE = "workspace"
YOUR_PROJECT_NAME = "pharma-realtime"
YOUR_PROJECT_DESCRIPTION = "Test project using Adult dataset."    

ws = RemoteWorkspace("http://35.88.54.181:5000/")
exist = ws.search_project(YOUR_PROJECT_NAME)
create_demo_project(ws,WORKSPACE,exist)