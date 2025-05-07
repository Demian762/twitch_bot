comandos_audios = {
    'holis':['holis'],
    'helldiver':['helldiver','helldivers','forsuperearth'],
    'cuervo':['cuervo'],
    'zazaraza':['zazaraza','indyforever','indy'],
    'piripipi':['piripipi','gg'],
    'dark':['dark'],
    'quiereme':['quiereme'],
    'sacrilegioso':['sacrilegioso','homero'],
    'sadsong':['sadsong','sad'],
    'Boca':['boca','bostero','boque'],
    'yeahbaby':['yeahbaby','yeababy','baby','larry','marit','marit887'],
    'wansaia82':['wansaia82','ariel','wansaia'],
    'presta':['red','presta','redfallen','theredfallen'],
}

comandos_mensajes = {
    'Boca':["boooooca booooooca","boca boca booooooca","booooooca boca boca"],
    'presta':["🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈🏳️‍🌈"],
    'horny':["yametekudasaaaaaaaai"],
}

autores_exclusivos = {
    'marit887':['yeahbaby'],
    'wansaia82':['wansaia82','wansaia'],
    'theredfallen':['presta']
}

comandos_general = [item for sublista in comandos_audios.values() for item in sublista] + list(comandos_audios.keys())