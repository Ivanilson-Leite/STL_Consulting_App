# app/mentor/routes.py
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime

# --- CORREÇÃO AQUI: Adicionado 'User' aos imports ---
from app.extensions import db
from app.models import User, Appointment, Carometro, UserTask, MentorAvailability, MentorLocation, ModuleResource, ModuleTask

mentor = Blueprint('mentor', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'pptx'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@mentor.route('/mentor_area')
@login_required
def mentor_area():
    return render_template('mentor/mentor_area.html')

@mentor.route('/profile')
@login_required
def profile():
    return render_template('mentor/profile.html')

@mentor.route('/modulo_01')
@login_required
def modulo_01():
    # 1. Agendamento
    appointment = Appointment.query.filter_by(user_id=current_user.id, module_name="Módulo 1").first()

    # 2. LÓGICA INTELIGENTE DE MENTOR E HORÁRIOS
    # Descobre quem é o mentor alvo (O do aluno OU o primeiro admin do sistema)
    target_mentor = current_user.my_mentor

    if not target_mentor:
        # Fallback: Se não tiver mentor vinculado, pega o primeiro admin
        # (Aqui estava o erro: User não estava importado)
        target_mentor = User.query.filter_by(role='mentor').first()

    from datetime import date
    available_slots = []

    if target_mentor:
        # Busca horários desse mentor específico
        available_slots = MentorAvailability.query.filter(
            MentorAvailability.mentor_id == target_mentor.id,
            MentorAvailability.is_booked == False,
            db.func.date(MentorAvailability.datetime_slot) >= date.today()
        ).order_by(MentorAvailability.datetime_slot).all()

    # 3. Lógica de Tarefas
    tasks_def = ModuleTask.query.filter_by(module_name='Módulo 1')\
        .order_by(ModuleTask.order_index, ModuleTask.title)\
        .all()

    user_deliveries = UserTask.query.filter_by(user_id=current_user.id).all()

    status_map_id = {t.task_id: t for t in user_deliveries if t.task_id is not None}
    status_map_name = {t.task_name: t for t in user_deliveries}

    tasks_data = []
    for t in tasks_def:
        delivery = status_map_id.get(t.id)
        if not delivery: delivery = status_map_name.get(t.title)
        if not delivery and "Carômetro" in t.title: delivery = status_map_name.get('Carometro')

        tasks_data.append({
            'def': t,
            'delivery': delivery,
            'status': delivery.status if delivery else 'Pendente'
        })

    # Passamos 'mentor_display' para o template usar o nome correto
    return render_template('mentor/modulo_01.html',
                           appointment=appointment,
                           available_slots=available_slots,
                           tasks_data=tasks_data,
                           mentor_display=target_mentor)

# --- ROTA: REALIZAR AGENDAMENTO ---
@mentor.route('/agendar', methods=['POST'])
@login_required
def schedule_appointment():
    if request.method == 'POST':
        module_name = request.form.get('module_name')
        new_slot_id = request.form.get('schedule_slot_id')
        notes = request.form.get('notes')

        if not new_slot_id:
            flash('Por favor, selecione um horário.', 'error')
            return redirect(url_for('mentor.modulo_01'))

        # 1. Busca o NOVO slot desejado
        new_slot = MentorAvailability.query.get(new_slot_id)

        if not new_slot or new_slot.is_booked:
            flash('Esse horário já foi reservado. Atualize a página.', 'error')
            return redirect(url_for('mentor.modulo_01'))

        # Formata dados visuais
        date_str = new_slot.datetime_slot.strftime('%d/%m/%Y às %H:%M')
        final_location = new_slot.location
        if new_slot.meeting_link:
            final_location += " (Link após confirmação)"

        # 2. Verifica se já existe agendamento (Reagendamento)
        existing_appt = Appointment.query.filter_by(user_id=current_user.id, module_name=module_name).first()

        try:
            if existing_appt:
                # --- LÓGICA DE LIBERAÇÃO DO HORÁRIO ANTIGO ---
                if existing_appt.availability_id:
                    old_slot = MentorAvailability.query.get(existing_appt.availability_id)
                    if old_slot:
                        old_slot.is_booked = False # LIBERA PARA OUTROS ALUNOS!
                # ---------------------------------------------

                # Atualiza com os dados do NOVO horário
                existing_appt.schedule_date = date_str
                existing_appt.location = final_location
                existing_appt.notes = notes
                existing_appt.status = 'Atualizado - Aguardando confirmação'
                existing_appt.availability_id = new_slot.id # VINCULA AO NOVO SLOT

                flash('Reagendamento solicitado! Seu horário antigo foi liberado.', 'success')
            else:
                # Cria novo agendamento
                new_appt = Appointment(
                    user_id=current_user.id,
                    module_name=module_name,
                    schedule_date=date_str,
                    location=final_location,
                    notes=notes,
                    availability_id=new_slot.id # VINCULA AO NOVO SLOT
                )
                db.session.add(new_appt)
                flash('Agendamento realizado com sucesso!', 'success')

            # 3. Marca o NOVO slot como ocupado
            new_slot.is_booked = True

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao agendar: {str(e)}', 'error')

        return redirect(url_for('mentor.modulo_01'))

# --- ROTA DE DOWNLOAD DE RECURSO (Para o Aluno) ---
@mentor.route('/resource/download/<int:res_id>')
@login_required
def download_resource(res_id):
    # Busca o recurso pelo ID
    resource = ModuleResource.query.get_or_404(res_id)

    # Define o diretório (assumindo a estrutura padrão que criamos)
    directory = os.path.join(current_app.root_path, 'static', 'arquivos', 'modulo_01', 'baixar')

    try:
        return send_from_directory(directory, resource.filename, as_attachment=True)
    except FileNotFoundError:
        flash('O arquivo solicitado não foi encontrado no servidor.', 'error')
        return redirect(url_for('mentor.modulo_01'))

# --- ROTAS DE ARQUIVOS (Mantidas) ---
@mentor.route('/download/material/<filename>')
@login_required
def download_material(filename):
    directory = os.path.join(current_app.root_path, 'static', 'arquivos', 'modulo_01', 'baixar')
    return send_from_directory(directory, filename, as_attachment=True)

@mentor.route('/upload/atividade', methods=['POST'])
@login_required
def upload_atividade():
    if 'file' not in request.files:
        flash('Nenhum arquivo enviado.', 'error')
        return redirect(url_for('mentor.modulo_01'))

    file = request.files['file']
    task_id = request.form.get('task_id') # ID da tarefa vindo do HTML

    if file.filename == '' or not task_id:
        flash('Erro: Arquivo ou identificação da tarefa ausente.', 'error')
        return redirect(url_for('mentor.modulo_01'))

    if file and allowed_file(file.filename):
        try:
            # 1. Busca a Definição da Tarefa
            task_def = ModuleTask.query.get(int(task_id))
            if not task_def:
                flash('Tarefa não encontrada no sistema.', 'error')
                return redirect(url_for('mentor.modulo_01'))

            # 2. Prepara o arquivo
            filename = secure_filename(file.filename)
            new_name = f"user_{current_user.id}_task_{task_id}_{filename}"
            save_dir = os.path.join(current_app.root_path, 'static', 'arquivos', 'modulo_01', 'recebido')
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)

            # Salva fisicamente
            file.save(os.path.join(save_dir, new_name))

            # 3. LÓGICA DE ATUALIZAÇÃO
            user_task = UserTask.query.filter_by(user_id=current_user.id, task_id=task_id).first()

            if not user_task:
                user_task = UserTask.query.filter_by(
                    user_id=current_user.id,
                    module_name=task_def.module_name,
                    task_name=task_def.title
                ).first()

            if user_task:
                user_task.task_id = task_id
                user_task.status = 'Concluído'
                user_task.file_path = new_name
                user_task.submitted_at = datetime.now()
            else:
                new_user_task = UserTask(
                    user_id=current_user.id,
                    task_id=task_id,
                    module_name=task_def.module_name,
                    task_name=task_def.title,
                    status='Concluído',
                    file_path=new_name,
                    submitted_at=datetime.now()
                )
                db.session.add(new_user_task)

            db.session.commit()
            flash('Atividade enviada com sucesso!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'Erro técnico ao salvar: {e}', 'error')

        return redirect(url_for('mentor.modulo_01'))

    flash('Tipo de arquivo não permitido (Use PDF ou PPTX).', 'error')
    return redirect(url_for('mentor.modulo_01'))

@mentor.route('/delete/atividade', methods=['POST'])
@login_required
def delete_atividade():
    task_id = request.form.get('task_id')

    if not task_id:
        flash('Erro de identificação.', 'error')
        return redirect(url_for('mentor.modulo_01'))

    user_task = UserTask.query.filter_by(user_id=current_user.id, task_id=task_id).first()

    if user_task:
        try:
            # 1. Remove arquivo físico
            if user_task.file_path:
                save_dir = os.path.join(current_app.root_path, 'static', 'arquivos', 'modulo_01', 'recebido')
                full_path = os.path.join(save_dir, user_task.file_path)
                if os.path.exists(full_path):
                    os.remove(full_path)

            # 2. Atualiza status para Pendente
            user_task.status = 'Pendente'
            user_task.file_path = None
            user_task.submitted_at = None

            db.session.commit()
            flash('Envio excluído. Você pode enviar um novo arquivo.', 'info')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir: {e}', 'error')

    return redirect(url_for('mentor.modulo_01'))
