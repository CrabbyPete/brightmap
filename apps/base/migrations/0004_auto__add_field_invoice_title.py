# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Invoice.title'
        db.add_column('base_invoice', 'title', self.gf('django.db.models.fields.CharField')(default='November 2011', max_length=255), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Invoice.title'
        db.delete_column('base_invoice', 'title')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'base.authorize': {
            'Meta': {'object_name': 'Authorize'},
            'customer_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payment_profile': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'profile_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'base.budget': {
            'Meta': {'object_name': 'Budget', '_ormbases': ['base.Term']},
            'remaining': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.cancel': {
            'Meta': {'object_name': 'Cancel', '_ormbases': ['base.Term']},
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.chapter': {
            'Meta': {'object_name': 'Chapter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['base.Letter']", 'null': 'True'}),
            'logo': ('django.db.models.fields.URLField', [], {'default': 'None', 'max_length': '200', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255'}),
            'organization': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Organization']"}),
            'organizer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'website': ('django.db.models.fields.URLField', [], {'default': 'None', 'max_length': '200', 'null': 'True'})
        },
        'base.connection': {
            'Meta': {'object_name': 'Connection'},
            'date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'sent'", 'max_length': '20'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Survey']"}),
            'term': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Term']"})
        },
        'base.connects': {
            'Meta': {'object_name': 'Connects', '_ormbases': ['base.Term']},
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'remaining': ('django.db.models.fields.IntegerField', [], {}),
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.count': {
            'Meta': {'object_name': 'Count', '_ormbases': ['base.Term']},
            'last_event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Event']", 'null': 'True', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {}),
            'remaining': ('django.db.models.fields.IntegerField', [], {}),
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.deal': {
            'Meta': {'object_name': 'Deal'},
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Chapter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Interest']"})
        },
        'base.event': {
            'Meta': {'object_name': 'Event'},
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Chapter']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'describe': ('django.db.models.fields.TextField', [], {}),
            'event_id': ('django.db.models.fields.BigIntegerField', [], {'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Letter']", 'null': 'True', 'blank': 'True'})
        },
        'base.eventbrite': {
            'Meta': {'object_name': 'Eventbrite'},
            'bot_email': ('django.db.models.fields.EmailField', [], {'default': 'None', 'max_length': '75', 'null': 'True'}),
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Chapter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'organizer_id': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45'}),
            'user_key': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45'})
        },
        'base.expire': {
            'Meta': {'object_name': 'Expire', '_ormbases': ['base.Term']},
            'date': ('django.db.models.fields.DateField', [], {}),
            'term_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['base.Term']", 'unique': 'True', 'primary_key': 'True'})
        },
        'base.interest': {
            'Meta': {'object_name': 'Interest'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'occupation': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'standard'", 'max_length': '20'})
        },
        'base.invoice': {
            'Meta': {'object_name': 'Invoice'},
            'cost': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '10', 'decimal_places': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issued': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'issued'", 'max_length': '20'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "'November 2011'", 'max_length': '255'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'base.leadbuyer': {
            'Meta': {'object_name': 'LeadBuyer'},
            'budget': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '2', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Letter']", 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'base.letter': {
            'Meta': {'object_name': 'Letter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'letter': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '255', 'null': 'True'})
        },
        'base.meetup': {
            'Meta': {'object_name': 'MeetUp'},
            'bot_email': ('django.db.models.fields.EmailField', [], {'default': 'None', 'max_length': '75', 'null': 'True'}),
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Chapter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'member_id': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45', 'null': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45', 'null': 'True'}),
            'token': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '45', 'null': 'True'})
        },
        'base.organization': {
            'Meta': {'object_name': 'Organization'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        },
        'base.profile': {
            'Meta': {'object_name': 'Profile'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'company': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_agreed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_attendee': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_leadbuyer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_organizer': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_ready': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'linkedin': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'newsletter': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'phone': ('django.contrib.localflavor.us.models.PhoneNumberField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'photo': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'twitter': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'website': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        'base.survey': {
            'Meta': {'object_name': 'Survey'},
            'attendee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Event']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'interest': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['base.Interest']", 'null': 'True'}),
            'mailed': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'base.term': {
            'Meta': {'object_name': 'Term'},
            'buyer': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'}),
            'cost': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '10', 'decimal_places': '2'}),
            'deal': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['base.Deal']"}),
            'exclusive': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '20'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['base']
