import boto3
import botocore
import os
import pandas as pd
from datetime import datetime
from botocore.exceptions import ClientError


class Envs:
    # Lambda ENN Vars from SAM Template
    table_name = os.environ.get("table_name")
    export_bucket = os.environ.get("export_bucket")


td = datetime.today().strftime('%Y-%m-%d')
dynamodb = boto3.client('dynamodb')
s3 = boto3.client("s3")
export_file = f'{td}-export.csv'


def dump_table(table_name):
    results = []
    last_evaluated_key = None
    while True:
        if last_evaluated_key:
            response = dynamodb.scan(
                TableName=table_name,
                ExclusiveStartKey=last_evaluated_key
            )
        else:
            response = dynamodb.scan(TableName=table_name)
        last_evaluated_key = response.get('LastEvaluatedKey')
        results.extend(response['Items'])
        if not last_evaluated_key:
            break
    return results


def lambda_handler(event, context):
    print('#### START - Event Received ####')
    print(event)
    try:
        data = dump_table(Envs.table_name)
        print(f"Items in list:   {len(data)}")
    except botocore.exceptions.ClientError as e:
        print(f"ERROR! - {e}")
    df = pd.DataFrame(data)
    print(f"Items           |             Count\n{df.count()}")
    print(f"\nRecord Count is:  {len(df.index)}")
    df.to_csv(f'/tmp/{export_file}', index=False, header=True)
    print(f'Exported to: /tmp/{export_file}')
    print(f'Uploading {export_file} to S3 Bucket: {Envs.export_bucket} ')
    try:
        s3.upload_file((f"/tmp/{export_file}"), Envs.export_bucket,
                       (f"{Envs.table_name}/{export_file}"))
    except botocore.exceptions.ClientError as e:
        print(f"ERROR! - {e}")
    print('#### DONE ####')
