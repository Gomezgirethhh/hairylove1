from django.contrib import admin
from django.http import HttpResponse
from openpyxl import Workbook
from .models import Mascota, Adopcion, Calificacion, Notificacion

@admin.register(Mascota)
class MascotaAdmin(admin.ModelAdmin):
    list_display = ('idMascota', 'Nombre_Mascota', 'Especie', 'Raza', 'Genero', 'Estado_Salud')
    list_filter = ('Especie', 'Raza', 'Genero', 'Estado_Salud', 'Esterilizado', 'Socializado')
    search_fields = ('Nombre_Mascota', 'Raza', 'Especie')
    readonly_fields = ('idMascota',)

@admin.register(Adopcion)
class AdopcionAdmin(admin.ModelAdmin):
    list_display = ('idAdopcion', 'idMascota', 'Estado', 'Fecha_Solicitud')
    list_filter = ('Estado', 'Fecha_Solicitud')
    search_fields = ('idMascota__Nombre_Mascota',)
    readonly_fields = ('idAdopcion',)
    actions = ['exportar_adopciones_excel']

    def exportar_adopciones_excel(self, request, queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = 'Adopciones'

        headers = ['ID', 'Mascota', 'Propietario', 'Criador', 'Estado', 'Solicitud', 'Adopción', 'Entrega', 'Motivo', 'Estado de solicitud', 'Control', 'Salud', 'Vivienda', 'Fuente']
        ws.append(headers)

        for adopcion in queryset:
            propietario = adopcion.idPropietario
            criador = adopcion.idCriador
            propietario_nombre = str(propietario) if propietario else 'N/A'
            criador_nombre = str(criador) if criador else 'N/A'
            ws.append([
                adopcion.idAdopcion,
                adopcion.idMascota.Nombre_Mascota,
                propietario_nombre,
                criador_nombre,
                adopcion.Estado,
                str(adopcion.Fecha_Solicitud),
                str(adopcion.Fecha_Adopción),
                str(adopcion.Fecha_Entrega),
                adopcion.Motivo_Adopción,
                adopcion.Estado_Solicitud,
                adopcion.Control_Adopción,
                adopcion.Estado_Salud_Mascota,
                adopcion.Lugar_Vivienda,
                adopcion.Fuente_Mascota,
            ])

        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = (max_length + 2)
            ws.column_dimensions[column].width = adjusted_width

        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename=adopciones_admin.xlsx'
        wb.save(response)
        return response

    exportar_adopciones_excel.short_description = 'Exportar adopciones seleccionadas a Excel'

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('idCalificacion', 'usuario_califica', 'usuario_calificado', 'puntuacion', 'fecha_creacion')
    list_filter = ('puntuacion', 'fecha_creacion')
    search_fields = ('usuario_califica__nombre', 'usuario_calificado__nombre')
    readonly_fields = ('idCalificacion', 'fecha_creacion')
    
    fieldsets = (
        ('Información de Calificación', {
            'fields': ('idCalificacion', 'adopcion', 'usuario_califica', 'usuario_calificado', 'puntuacion', 'comentario', 'fecha_creacion')
        }),
    )

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('idNotificacion', 'usuario', 'tipo_con_icono', 'titulo_truncado', 'leido_badge', 'fecha_creacion')
    list_filter = ('tipo', 'leido', 'fecha_creacion')
    search_fields = ('usuario__nombre', 'titulo', 'mensaje')
    readonly_fields = ('idNotificacion', 'fecha_creacion', 'relacionado_con', 'adopcion')
    
    fieldsets = (
        ('Información General', {
            'fields': ('idNotificacion', 'usuario', 'tipo', 'leido', 'fecha_creacion')
        }),
        ('Contenido', {
            'fields': ('titulo', 'mensaje')
        }),
        ('Contexto', {
            'fields': ('adopcion', 'relacionado_con', 'enlace_accion')
        }),
    )
    
    def tipo_con_icono(self, obj):
        tipos_display = {
            'calificacion': 'Calificacion',
            'solicitud_adopcion': 'Solicitud de Adopcion',
            'adopcion_aprobada': 'Adopcion Aprobada',
            'adopcion_rechazada': 'Adopcion Rechazada',
        }
        tipo_texto = tipos_display.get(obj.tipo, obj.get_tipo_display())
        return tipo_texto
    tipo_con_icono.short_description = 'Tipo'
    
    def titulo_truncado(self, obj):
        return obj.titulo[:50] + '...' if len(obj.titulo) > 50 else obj.titulo
    titulo_truncado.short_description = 'Título'
    
    def leido_badge(self, obj):
        if obj.leido:
            return 'Leido'
        return 'Nuevo'
    leido_badge.short_description = 'Estado'
    
    actions = ['marcar_como_leido', 'marcar_como_no_leido']
    
    def marcar_como_leido(self, request, queryset):
        updated = queryset.update(leido=True)
        self.message_user(request, f'{updated} notificación(es) marcada(s) como leída(s)')
    marcar_como_leido.short_description = 'Marcar como leído'
    
    def marcar_como_no_leido(self, request, queryset):
        updated = queryset.update(leido=False)
        self.message_user(request, f'{updated} notificación(es) marcada(s) como no leída(s)')
    marcar_como_no_leido.short_description = 'Marcar como no leído'
