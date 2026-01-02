
import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class Query(CRMQuery, graphene.ObjectType):
    """Main GraphQL query combining all app queries."""
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    """Main GraphQL mutation combining all app mutations."""
    pass

# Create schema with both query and mutation
schema = graphene.Schema(query=Query, mutation=Mutation)