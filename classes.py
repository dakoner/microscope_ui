

# By convention, our non-background classes start counting at 1.  Given
# that we will be predicting just one class, we will therefore assign it a
# `class id` of 1.
tardigrade_class_id = 1
algae_class_id = 2
egg_class_id = 3
moult_class_id = 4
vorticella_class_id = 5
animacule_class_id = 6
junk_class_id = 7

num_classes = 7
category_index = {
    tardigrade_class_id: {'id': tardigrade_class_id, 'name': 'tardigrade'},
    algae_class_id: {'id': algae_class_id, 'name': 'algae'},
     egg_class_id: {'id': egg_class_id, 'name': 'egg'},
     moult_class_id: {'id': moult_class_id, 'name': 'moult'},
     vorticella_class_id: {'id': vorticella_class_id, 'name': 'vorticella'},
     animacule_class_id: {'id': animacule_class_id, 'name': 'animacule'},
     junk_class_id: {'id': junk_class_id, 'name': 'junk_class'},
}


name_to_id = {
    'tardigrade': 1,
    'algae': 2,
    'egg': 3,
    'moult': 4,
    'vorticella': 5,
    'animacule': 6,
    'junk': 7
}


id_to_name = {
    1: 'tardigrade',
    2: 'algae',
    3: 'egg',
    4: 'moult',
    5: 'vorticella',
    6: 'animacule',
    7: 'junk',
}