from django.contrib import admin
from django.utils.html import format_html
from app.models import (
    Creator,
    Listener,
    Library,
    Form,
    Song,
    Share,
    CreditTransaction,
)
from app.services.generation_service import generate_song_from_form


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "creator",
        "genre",
        "mood",
        "requested_title",
        "requested_duration_seconds",
        "created_at",
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            generate_song_from_form(obj)


@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    filter_horizontal = ("songs",)

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    list_display = ("id", "song", "token", "clickable_share_link", "created_at")
    readonly_fields = ("token", "clickable_share_link", "created_at")

    def clickable_share_link(self, obj):
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.share_link,
            obj.share_link
        )

    clickable_share_link.short_description = "Share Link"

admin.site.register(Creator)
admin.site.register(Listener)
admin.site.register(Song)
admin.site.register(CreditTransaction)