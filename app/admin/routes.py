# app/admin/routes.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models import User, UserTask, Appointment, MentorAvailability, ModuleResource, MentorLocation, ModuleTask
from app.admin.decorators import mentor_required
from datetime import datetime

admin = Blueprint('admin', __name__, url_prefix='/admin')

@admin.route('/dashboard')
@login_required
@mentor_required
def dashboard():
    # 1. LISTA DE MENTORADOS (PRIVADO)
    # Cada mentor vê apenas os alunos vinculados a ele
    mentees = User.query.filter_by(role='mentee', mentor_id=current_user.id).all()

    # 2. TAREFAS RECENTES (COMUM)
    # Mostra todas as entregas do sistema, permitindo gestão compartilhada
    recent_tasks = UserTask.query.filter_by(status='Concluído')\
        .order_by(UserTask.submitted_at.desc())\
        .all()

    # 3. AGENDAMENTOS (PRIVADO)
    # Filtra agendamentos apenas dos alunos deste mentor
    pending_appointments = Appointment.query.join(User).filter(
        User.mentor_id == current_user.id,
        Appointment.status.in_(['Aguardando confirmação', 'Atualizado - Aguardando confirmação'])
    ).all()

    all_appointments = Appointment.query.join(User).filter(
        User.mentor_id == current_user.id
    ).order_by(Appointment.schedule_date.desc()).all()

    # 4. RECURSOS / MATERIAIS (COMUM)
    # Todos os mentores veem e usam os mesmos materiais
    resources = ModuleResource.query.all()

    # 5. LOCAIS E AGENDA (PRIVADO)
    # Cada mentor gerencia sua própria disponibilidade e locais
    my_locations = MentorLocation.query.filter_by(mentor_id=current_user.id).all()

    from datetime import date

    open_slots = MentorAvailability.query.filter(
        MentorAvailability.mentor_id == current_user.id,
        MentorAvailability.is_booked == False,
        # Compara apenas a DATA (YYYY-MM-DD), ignorando a hora para evitar sumiço
        db.func.date(MentorAvailability.datetime_slot) >= date.today()
    ).order_by(MentorAvailability.datetime_slot).all()

    # 6. DEFINIÇÃO DE TAREFAS (COMUM)
    module_tasks = ModuleTask.query.order_by(ModuleTask.module_name, ModuleTask.order_index).all()

    return render_template('admin/dashboard.html',
                           mentees=mentees,
                           recent_tasks=recent_tasks,
                           pending_appointments=pending_appointments,
                           all_appointments=all_appointments,
                           resources=resources,
                           my_locations=my_locations,
                           open_slots=open_slots,
                           module_tasks=module_tasks)

# --- NOVA ROTA: CRIAR TAREFA ---
@admin.route('/task/create', methods=['POST'])
@login_required
@mentor_required
def create_task():
    module_name = request.form.get('module_name')
    title = request.form.get('title')
    description = request.form.get('description')
    resource_id = request.form.get('resource_id')
    external_link = request.form.get('external_link')
    allow_upload = True if request.form.get('allow_upload') else False

    # NOVO: Recebe a ordem do formulário (padrão 0 se vazio)
    order_index = request.form.get('order_index', 0, type=int)

    if not resource_id or resource_id == "":
        resource_id = None

    new_task = ModuleTask(
        module_name=module_name,
        title=title,
        description=description,
        resource_id=resource_id,
        external_link=external_link,
        allow_upload=allow_upload,
        order_index=order_index # <--- Salva aqui
    )

    db.session.add(new_task)
    db.session.commit()
    flash('Nova tarefa configurada com sucesso!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/task/delete_def/<int:task_id>')
@login_required
@mentor_required
def delete_task_definition(task_id):
    task = ModuleTask.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    flash('Tarefa removida do módulo.', 'info')
    return redirect(url_for('admin.dashboard'))

@admin.route('/task/edit/<int:task_id>', methods=['POST'])
@login_required
@mentor_required
def edit_task_definition(task_id):
    task = ModuleTask.query.get_or_404(task_id)

    # Atualiza os campos básicos
    task.module_name = request.form.get('module_name')
    task.title = request.form.get('title')
    task.description = request.form.get('description')
    task.external_link = request.form.get('external_link')

    # Atualiza ordem
    task.order_index = request.form.get('order_index', 0, type=int)

    # Lógica do Checkbox (se não vier no request, é False)
    task.allow_upload = True if request.form.get('allow_upload') else False

    # Lógica do Resource ID (pode ser vazio)
    resource_id = request.form.get('resource_id')
    if resource_id and resource_id != "":
        task.resource_id = int(resource_id)
    else:
        task.resource_id = None

    try:
        db.session.commit()
        flash('Tarefa atualizada com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao atualizar tarefa.', 'error')
        print(f"Erro edit_task_definition: {e}")

    return redirect(url_for('admin.dashboard'))

# --- NOVO: Rota para Excluir Horário Livre ---
@admin.route('/agenda/delete/<int:slot_id>')
@login_required
@mentor_required
def delete_availability(slot_id):
    slot = MentorAvailability.query.get_or_404(slot_id)
    if slot.mentor_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin.dashboard'))

    # Só permite excluir se não estiver agendado (ou force se preferir)
    if slot.is_booked:
        flash('Não é possível excluir um horário que já foi reservado por um aluno.', 'warning')
        return redirect(url_for('admin.dashboard'))

    db.session.delete(slot)
    db.session.commit()
    flash('Horário removido da agenda.', 'info')
    return redirect(url_for('admin.dashboard'))

# --- NOVO: Rota para Editar Local (Update) ---
@admin.route('/location/edit/<int:loc_id>', methods=['POST'])
@login_required
@mentor_required
def edit_location(loc_id):
    loc = MentorLocation.query.get_or_404(loc_id)
    if loc.mentor_id != current_user.id:
        abort(403)

    loc.name = request.form.get('loc_name')
    loc.type = request.form.get('loc_type')

    if loc.type == 'online':
        loc.address = None
    else:
        loc.address = request.form.get('loc_address')

    db.session.commit()
    flash('Local atualizado com sucesso.', 'success')
    return redirect(url_for('admin.dashboard'))

# --- GESTÃO DE USUÁRIOS ---
@admin.route('/user/toggle_status/<int:user_id>')
@login_required
@mentor_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    user.active = not user.active
    db.session.commit()
    flash(f'Status do usuário {user.username} atualizado.', 'success')
    return redirect(url_for('admin.dashboard'))

# --- GESTÃO DE TAREFAS ---
@admin.route('/task/download/<int:task_id>')
@login_required
@mentor_required
def download_user_task(task_id):
    # Busca a tarefa do aluno
    task = UserTask.query.get_or_404(task_id)

    # Caminho onde os alunos salvam os arquivos (RECEBIDO)
    # Nota: Se no futuro tiver mais módulos, essa pasta 'modulo_01' deve virar dinâmica
    directory = os.path.join(current_app.root_path, 'static', 'arquivos', 'modulo_01', 'recebido')

    try:
        return send_from_directory(directory, task.file_path, as_attachment=True)
    except FileNotFoundError:
        flash('O arquivo não foi encontrado no servidor (pode ter sido removido).', 'error')
        return redirect(url_for('admin.dashboard'))

# --- GESTÃO DE LOCAIS ---
@admin.route('/location/add', methods=['POST'])
@login_required
@mentor_required
def add_location():
    name = request.form.get('loc_name')
    loc_type = request.form.get('loc_type') # 'presencial' ou 'online'
    address = request.form.get('loc_address')

    if loc_type == 'online':
        address = None # Online não tem endereço físico fixo no cadastro (link é por horário)

    new_loc = MentorLocation(mentor_id=current_user.id, name=name, type=loc_type, address=address)
    db.session.add(new_loc)
    db.session.commit()

    flash('Novo local cadastrado com sucesso!', 'success')
    return redirect(url_for('admin.dashboard'))

@admin.route('/location/delete/<int:loc_id>')
@login_required
@mentor_required
def delete_location(loc_id):
    loc = MentorLocation.query.get_or_404(loc_id)
    if loc.mentor_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('admin.dashboard'))

    db.session.delete(loc)
    db.session.commit()
    flash('Local removido.', 'info')
    return redirect(url_for('admin.dashboard'))

# --- GESTÃO DE AGENDA (ATUALIZADO) ---
@admin.route('/agenda/add', methods=['POST'])
@login_required
@mentor_required
def add_availability():
    date_str = request.form.get('datetime_slot')
    location_id = request.form.get('location_id')
    meeting_link = request.form.get('meeting_link')

    try:
        dt_obj = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')

        # Busca detalhes do local para salvar histórico
        loc_obj = MentorLocation.query.get(location_id)
        loc_name = loc_obj.name if loc_obj else "Desconhecido"

        slot = MentorAvailability(
            mentor_id=current_user.id,
            datetime_slot=dt_obj,
            location_id=location_id,
            location=loc_name, # Backup textual
            meeting_link=meeting_link if loc_obj.type == 'online' else None
        )

        db.session.add(slot)
        db.session.commit()
        flash('Horário disponibilizado na agenda do aluno.', 'success')
    except Exception as e:
        flash(f'Erro ao salvar horário: {e}', 'error')

    return redirect(url_for('admin.dashboard'))

@admin.route('/appointment/action/<int:appt_id>/<action>')
@login_required
@mentor_required
def appointment_action(appt_id, action):
    appt = Appointment.query.get_or_404(appt_id)

    if action == 'confirm':
        appt.status = 'Confirmado'
        # Se confirmado, o slot continua is_booked = True (Correto)
        flash('Agendamento confirmado!', 'success')

    elif action == 'reject':
        appt.status = 'Recusado'

        # --- LÓGICA DE LIBERAÇÃO AO RECUSAR ---
        if appt.availability_id:
            slot = MentorAvailability.query.get(appt.availability_id)
            if slot:
                slot.is_booked = False # O horário volta a ficar livre na dashboard
        # --------------------------------------

        flash('Agendamento recusado e horário liberado na agenda.', 'warning')

    db.session.commit()
    return redirect(url_for('admin.dashboard'))

# --- GESTÃO DE RECURSOS (MODELOS) ---
@admin.route('/resource/upload', methods=['POST'])
@login_required
@mentor_required
def upload_resource():
    file = request.files.get('file')
    module_name = request.form.get('module_name')
    title = request.form.get('title')

    if file:
        filename = secure_filename(file.filename)
        # Salva na pasta de baixar do módulo específico
        save_dir = os.path.join(current_app.root_path, 'static', 'arquivos', 'modulo_01', 'baixar')
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        file.save(os.path.join(save_dir, filename))

        resource = ModuleResource(mentor_id=current_user.id, module_name=module_name, title=title, filename=filename)
        db.session.add(resource)
        db.session.commit()
        flash('Modelo enviado com sucesso.', 'success')

    return redirect(url_for('admin.dashboard'))

@admin.route('/resource/download/<int:res_id>')
@login_required
@mentor_required
def download_resource(res_id):
    res = ModuleResource.query.get_or_404(res_id)

    # Nota: Estamos assumindo o caminho padrão definido no upload.
    # Idealmente, o caminho deveria ser dinâmico baseado no módulo, mas seguiremos a lógica atual.
    directory = os.path.join(current_app.root_path, 'static', 'arquivos', 'modulo_01', 'baixar')

    try:
        return send_from_directory(directory, res.filename, as_attachment=True)
    except FileNotFoundError:
        flash('Arquivo físico não encontrado.', 'error')
        return redirect(url_for('admin.dashboard'))

@admin.route('/resource/delete/<int:res_id>')
@login_required
@mentor_required
def delete_resource(res_id):
    res = ModuleResource.query.get_or_404(res_id)

    # 1. Tenta remover o arquivo físico
    directory = os.path.join(current_app.root_path, 'static', 'arquivos', 'modulo_01', 'baixar')
    full_path = os.path.join(directory, res.filename)

    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except Exception as e:
            print(f"Erro ao deletar arquivo: {e}")

    # 2. Remove do banco de dados
    db.session.delete(res)
    db.session.commit()

    flash('Material removido com sucesso.', 'info')
    return redirect(url_for('admin.dashboard'))
