from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_ingredient_product_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE api_ingredient DROP CONSTRAINT IF EXISTS api_ingredient_product_id_key;",
            reverse_sql="ALTER TABLE api_ingredient ADD CONSTRAINT api_ingredient_product_id_key UNIQUE (product_id);",
        ),
    ]
