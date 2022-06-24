def check_form_fields(form_fields, form):
    for field in form_fields:
        if field not in form.keys():
            return False, field

    return True, ""