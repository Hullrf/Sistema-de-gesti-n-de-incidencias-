"""
Script para poblar la base de datos con datos iniciales.
Ejecutar una sola vez: python seed.py
"""
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.incident import Incident, StatusEnum

app = create_app()

with app.app_context():
    db.create_all()

    # Admin
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        print("Usuario admin creado  (pass: admin123)")

    # Usuario regular
    if not User.query.filter_by(username='usuario1').first():
        user = User(username='usuario1', role='user')
        user.set_password('pass123')
        db.session.add(user)
        print("Usuario usuario1 creado  (pass: pass123)")

    db.session.commit()

    admin = User.query.filter_by(username='admin').first()
    user  = User.query.filter_by(username='usuario1').first()

    samples = [
        ('Red caída en laboratorio A',    'Sin conexión desde las 9am.',           StatusEnum.PENDIENTE,  admin.id),
        ('PC no enciende en aula 3',       'Falla de alimentación eléctrica.',      StatusEnum.EN_PROCESO, admin.id),
        ('Proyector con imagen distorsionada', 'Colores incorrectos desde ayer.',   StatusEnum.RESUELTO,   admin.id),
        ('Impresora atascada sala sistemas', 'Papel atascado en bandeja 2.',        StatusEnum.PENDIENTE,  user.id),
        ('Solicitud de software estadístico', 'Requiere SPSS para laboratorio.',    StatusEnum.EN_PROCESO, user.id),
    ]

    for title, desc, status, uid in samples:
        if not Incident.query.filter_by(title=title).first():
            db.session.add(Incident(title=title, description=desc, status=status, user_id=uid))
            print(f"  + Incidencia: {title}")

    db.session.commit()
    print("\nSeed completado exitosamente.")
