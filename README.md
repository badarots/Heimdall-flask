# Heimdall

Esse é um rascunho do controlador da fechadura da sala do HackerSpace.IFUSP. Foi criado um site simples (usando Flask) com cadastro de usuários que se comunica (usando o protocolo MQTT) com um outro dispositivo que libera a fechadura da porta.

## Instalando localmente

Você pode instalar o serviço localmente no seu computador para testa-lo. Primeiro vai precisar instalar todas as dependências.

### Instalando dependências usando pipenv

Recomendo usar o ``pipenv`` para gerar um ambiente virtual para teste. Primeiro certifique-se que o ``pip`` está atualizado, em seguida instale o ``pipenv``.

    $ pip install -U pip
    $ pip install pipenv

Na pasta do repositório crie o ambiente e instale os pacotes necessários (listados no arquivo ``Pipfile``).

    $ pipenv --three
    $ pipenv install

Agora você já tem um ambiente virtual com todos as dependências necessárias. Mas precisa acessá-lo antes de executar qualquer comando. Com o comando abaixo você entre nesse ambiente.

    $ pipenv shell

### Iniciando o banco de dados

Para rodar o site corretamente você precisa criar o banco de dados que será usado pelo servidor para guardar os dados de usuários e log deabertura da porta.

No ambiente virtual execute o seguinte para criar um banco de dados vazio:

    $ flask db init
    $ flask db migrate -m "init"
    $ flask db upgrade

### Simulando servidor de e-mails

O serviço envia e-mails para os usuários em dois casos: para ativar um usuário recém cadastrado e para recuperar um senha esquecida. Para essas coisas funcionarem você precisa emular um servidor de e-mail que finge enviar e receber esses e-mails (para não precisar configurar um serviço de e-mail real).

Para ativar esse servidor execute

    $  python -m smtpd -n -c DebuggingServer localhost:8025

Não feche esse terminal, ele precisa continuar executando para simular o envio das mensagens. As mensagens envidas apareceram nessa tela.

### Rodando o serviço (finalmente)

Agora já pode rodar o serviço

    $ flask run

E para abrir o site digite este endereço em seu navegador

    localhost:5000

## Funcionalidades

O site é ainda muito simples mas o básico já está funcionando. Os usuários se cadastram com um email que é usado para enviar um link de ativação para a conta. Com a conta a ativa o usuário pode liberar a porta.

Outra coisa que já foi implementada é a alteração de uma senha esquecida. Funciona da mesma forma que a ativação por e-mail. O usuário recebe um link que lhe dá o poder de alterar sua senha.

O serviço é uma adaptação desse tutorial: [The Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

Pra entender o que está contecendo o melhor é ler o que está lá. Principalmente os capítulos 1 ao 5, 6 e 10.

## Autenticação das mensagems (em construção)

As mensgagens envidas por MQTT serão autenticadas para garantir sua oringem.

### Vai funcionar assim

Vamos enviar uma mensagem ``m``. A mensagem será enviada sem encriptação acompanhada de uma assinatura ``s``, separados pelo caractere ``$``, para validá-la. Essa assinatura será uma hash gerada pela mensagem e uma chave ``k`` secreta, conhecida pelo servidor e pelo cliente. Assim o pacote terá esse formato:

    payload = m + '$' + s(m,k)

Assim que recebemos o pacote testamos se ele está firmeza gerando a assinatura ``s(m,k)`` e comparando com o a que foi enviada.

### Gerando a assinatura ``s(m, k)``

A assinatura será gerando usando HMAC com sha256: [Python](https://docs.python.org/3.7/library/hmac.html#module-hmac) [Arduino](http://rweather.github.io/arduinolibs/crypto.html)

Decodificanda usando base64: [Python](https://docs.python.org/3.7/library/base64.html) [Arduino](https://github.com/Densaugeo/base64_arduino)

### Exemplo

O pacote completo terá essa forma:

    liberar:1544721462$nWvF9/DLIo8l3OMcKqUvY9EUTP+71TIMzIlxS2lnsJE=

A mensagem é tudo antes do ``$``: ``liberar:1544721462``. Possui o comando ``liberar`` e um timestamp indicando quando foi gerada, separados por um ``:``. O restante é a assinatura decodificada em base64.
