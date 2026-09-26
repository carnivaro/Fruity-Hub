import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('store', '0004_contactmessage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('Cash on Delivery', 'Cash on Delivery'),
                    ('Card (Test Mode)', 'Card (Test Mode)'),
                ],
                default='Cash on Delivery',
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('cod', 'Pay on delivery'),
                    ('awaiting_payment', 'Awaiting payment'),
                    ('paid', 'Paid'),
                    ('failed', 'Payment failed'),
                ],
                default='cod',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='card_last4',
            field=models.CharField(blank=True, max_length=4),
        ),
        migrations.CreateModel(
            name='ReturnRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.CharField(choices=[
                    ('damaged', 'Damaged during delivery'),
                    ('wrong_item', 'Wrong item received'),
                    ('missing_item', 'Item(s) missing from order'),
                    ('quality_issue', 'Poor product quality'),
                    ('other', 'Other'),
                ], default='damaged', max_length=20)),
                ('description', models.TextField()),
                ('photo', models.ImageField(blank=True, null=True, upload_to='returns/')),
                ('status', models.CharField(choices=[
                    ('submitted', 'Submitted'),
                    ('under_review', 'Under review'),
                    ('approved', 'Approved'),
                    ('rejected', 'Rejected'),
                    ('resolved', 'Resolved'),
                ], default='submitted', max_length=20)),
                ('admin_response', models.TextField(blank=True, help_text='Visible to the customer once added.')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_requests', to='store.order')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='return_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
