# Etapa 2 - Identidade e multi-tenancy

## Objetivo

Estabelecer a fronteira de segurança que será usada por aplicações, destinos e
eventos nas próximas etapas. Todo recurso futuro deverá pertencer a uma
organização e ser acessado por um usuário autenticado dessa mesma organização.

## Escopo

- cadastro atômico de organização e usuário proprietário;
- autenticação por e-mail e senha com token JWT de curta duração;
- hash de senha Argon2id;
- consulta do usuário autenticado e da organização atual;
- alteração do nome da organização apenas pelo proprietário;
- criação de membros apenas pelo proprietário;
- listagem de usuários limitada à organização do token;
- migração Alembic para organizações e usuários;
- testes de autorização, conflito e isolamento entre organizações.

## Decisões

- O e-mail é globalmente único nesta etapa para permitir login sem solicitar o
  slug da organização.
- O slug é imutável e globalmente único porque será um identificador estável.
- Cada usuário pertence a uma única organização. Uma tabela de associações só
  será introduzida caso o produto passe a exigir participação em várias contas.
- O cadastro cria exatamente um proprietário. Novos usuários entram como
  membros; promoção e transferência de propriedade ficam fora desta etapa.
- O token contém os identificadores do usuário e da organização. A API ainda
  confirma ambos no banco para impedir uso de tokens com tenant adulterado.

## Fora do escopo

- recuperação de senha, verificação de e-mail e convites por e-mail;
- autenticação social ou multifator;
- aplicações, endpoints de destino e chaves de API;
- eventos de webhook, filas, tentativas e retentativas;
- cobrança e limites por plano.

Esses limites mantêm a etapa pequena, auditável e segura antes do domínio de
entrega de webhooks.
