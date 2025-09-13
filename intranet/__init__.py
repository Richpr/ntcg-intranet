def __init__(self, *args, **kwargs):
    user = kwargs.pop('user', None)
    super().__init__(*args, **kwargs)
    if user:
        self.fields['nationalite'].queryset = user.managed_countries.all() if user.managed_countries.exists() else Country.objects.all()