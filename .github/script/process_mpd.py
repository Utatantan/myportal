import os
import json
import yaml
import glob
from datetime import datetime
import sys

class ValidationError(Exception):
    pass

def validate_data(data, file_path):
    errors = []
    
    # 必須フィールドの確認
    required_fields = ['title', 'url']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # 日付フィールドの型チェック
    try:
        if 'year' in data and not (isinstance(data['year'], int) and 1900 <= data['year'] <= 2100):
            errors.append(f"Invalid year: {data['year']} (must be between 1900 and 2100)")
        if 'month' in data and not (isinstance(data['month'], int) and 1 <= data['month'] <= 12):
            errors.append(f"Invalid month: {data['month']} (must be between 1 and 12)")
        if 'date' in data and not (isinstance(data['date'], int) and 1 <= data['date'] <= 31):
            errors.append(f"Invalid date: {data['date']} (must be between 1 and 31)")
        if 'time' in data:
            datetime.strptime(data['time'], "%H:%M:%S")
    except ValueError as e:
        errors.append(f"Invalid date/time format: {str(e)}")
    
    # URLの形式チェック
    if data.get('url') and not data['url'].startswith(('http://', 'https://')):
        errors.append(f"Invalid URL format: {data['url']}")
    
    # タグの形式チェック
    if 'tags' in data:
        if not isinstance(data['tags'], list):
            errors.append("Tags must be a list")
        else:
            for tag in data['tags']:
                if not isinstance(tag, str):
                    errors.append(f"Invalid tag format: {tag}")
    
    if errors:
        error_message = f"\nValidation errors in {file_path}:\n" + "\n".join(f"- {error}" for error in errors)
        raise ValidationError(error_message)

def process_mpd_files():
    # 出力ディレクトリの作成
    os.makedirs('data', exist_ok=True)
    
    # すべての.mpdファイルを取得
    mpd_files = glob.glob('item/**/*.mpd', recursive=True)
    has_errors = False
    items = []
    
    for file_path in mpd_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # YAMLとして解析
                try:
                    data = yaml.safe_load(content)
                    validate_data(data, file_path)
                    
                    # デフォルト値の設定
                    now = datetime.now()
                    if not data.get('year'):
                        data['year'] = now.year
                    if not data.get('month'):
                        data['month'] = now.month
                    if not data.get('date'):
                        data['date'] = now.day
                    if not data.get('time'):
                        data['time'] = now.strftime("%H:%M:%S")
                    if not data.get('tags'):
                        data['tags'] = []
                    
                    # ファイル名をIDとして追加
                    data['id'] = os.path.basename(file_path).replace('.mpd', '')
                    
                    # ソート用の統合された日時文字列を作成
                    sort_date = f"{data['year']:04d}-{data['month']:02d}-{data['date']:02d}T{data['time']}"
                    data['_sort_date'] = sort_date
                    
                    items.append(data)
                    
                except yaml.YAMLError as e:
                    print(f"❌ YAML parsing error in {file_path}:\n{str(e)}", file=sys.stderr)
                    has_errors = True
                except ValidationError as e:
                    print(f"❌ {str(e)}", file=sys.stderr)
                    has_errors = True
                    
        except Exception as e:
            print(f"❌ Unexpected error processing {file_path}:\n{str(e)}", file=sys.stderr)
            has_errors = True
    
    if has_errors:
        sys.exit(1)
    
    # 日付でソート（新しい順）
    items.sort(key=lambda x: x.get('_sort_date', ''), reverse=True)
    
    # ソート用の一時フィールドを削除
    for item in items:
        item.pop('_sort_date', None)
    
    # JSONファイルに保存
    with open('data/items.json', 'w', encoding='utf-8') as f:
        json.dump({'items': items}, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Successfully processed {len(items)} items and saved to data/items.json")

if __name__ == "__main__":
    process_mpd_files()