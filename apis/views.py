from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import FixingCommit, FixedFile, Repository, Task
from .serializers import FixingCommitSerializer, FixedFileSerializer, RepositorySerializer, TaskSerializer


class RepositoriesViewSet(viewsets.ViewSet):
    """
    API endpoint that allows repositories to be viewed or edited.

    list:
    Retrieve all the repositories.

    retrieve:
    Retrieve a repository.

    create:
    Create a repository.

    partial_update:
    Update one or more fields on an existing repository.

    destroy:
    Delete a repository.
    """

    def list(self, request):
        repositories = Repository.objects.all()
        serializer = RepositorySerializer(repositories, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        repository = get_object_or_404(Repository, id=pk)
        serializer = RepositorySerializer(repository)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):

        try:  # to get the repository, if exists
            repository = Repository.objects.get(id=request.data.get('id', None))
            return Response(status=status.HTTP_409_CONFLICT)
        except Repository.DoesNotExist:
            serializer = RepositorySerializer(data=request.data)

            if not request.data.get('id'):
                return Response({'message': 'id is missing'}, status=status.HTTP_400_BAD_REQUEST)
            elif not request.data.get('full_name'):
                return Response({'message': 'full_name is missing'}, status=status.HTTP_400_BAD_REQUEST)
            elif not request.data.get('url'):
                return Response({'message': 'url is missing'}, status=status.HTTP_400_BAD_REQUEST)
            elif serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, pk=None):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk=None):
        try:  # to get the repository, if exists
            repository = Repository.objects.get(id=pk)
            repository.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Repository.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


# ===================================== FIXING COMMITS ===============================================================#

class FixingCommitsViewSet(viewsets.ViewSet):
    """
    API endpoint that allows fixing-commits to be viewed or edited.

    list:
    Retrieve all the fixing-commits.

    retrieve:
    Retrieve a fixing-commit.

    create:
    Create a fixing-commit.

    partial_update: Set up the is_false_positive field of a fixing-commit. If is_false_positive equals False,
    then it switches to True, and vice-versa.

    destroy:
    Delete a fixing-commit.
    """

    def list(self, request):
        repository = self.request.query_params.get('repository', None)

        if repository:
            fixing_commits = FixingCommit.objects.filter(repository=repository)
        else:
            fixing_commits = FixingCommit.objects.all()

        serializer = FixingCommitSerializer(fixing_commits, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        fixing_commit = get_object_or_404(FixingCommit, sha=pk)
        serializer = FixingCommitSerializer(fixing_commit)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):

        try:  # to get the fixing-commit, if exists
            FixingCommit.objects.get(sha=request.data.get('sha', None))
            return Response(status=status.HTTP_409_CONFLICT)
        except FixingCommit.DoesNotExist:
            if not request.data.get('sha'):
                return Response('Primary key \'sha\' is missing.', status=status.HTTP_400_BAD_REQUEST)

            serializer = FixingCommitSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer.save()
                return Response(status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk):
        fixing_commit = get_object_or_404(FixingCommit, sha=pk)
        fixing_commit.is_false_positive = not fixing_commit.is_false_positive
        fixing_commit.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        fixing_commit = get_object_or_404(FixingCommit, sha=pk)
        fixing_commit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ===================================== FIXED FILES ===============================================================#

class FixedFilesViewSet(viewsets.ViewSet):
    """
    API endpoint that allows fixed-files to be viewed or edited.

    list:
    Retrieve all the fixed-files.

    retrieve: NOT IMPLEMENTED

    create:
    Create a fixing-file.

    partial_update: Set up the is_false_positive field of a fixed-file. If is_false_positive equals False,
    then it switches to True, and vice-versa.

    destroy:
    Delete a fixing-file.
    """

    def list(self, request):
        fixing_commit = self.request.query_params.get('fixing_commit', None)
        repository = self.request.query_params.get('repository', None)

        if fixing_commit and repository:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        elif fixing_commit:
            fixed_files = FixedFile.objects.filter(fixing_commit=fixing_commit)

        elif repository:
            fixing_commits = FixingCommit.objects.filter(repository=repository)
            fixing_commits = [commit.sha for commit in list(fixing_commits) if not commit.is_false_positive]
            fixed_files = FixedFile.objects.filter(fixing_commit__in=fixing_commits)

        else:
            fixed_files = FixedFile.objects.all()

        serializer = FixedFileSerializer(fixed_files, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def create(self, request):
        try:  # to get the fixing-file, if exists
            FixedFile.objects.get(filepath=request.data.get('filepath', None),
                                  bug_inducing_commit=request.data.get('bug_inducing_commit', None),
                                  fixing_commit=request.data.get('fixing_commit', None))
            return Response(status=status.HTTP_409_CONFLICT)
        except FixedFile.DoesNotExist:
            if not (request.data.get('filepath') and request.data.get('bug_inducing_commit') and request.data.get('fixing_commit')):
                return Response('One or more among (filepath, bug_inducing_commit, fixing_commit) is missing.',
                                status=status.HTTP_400_BAD_REQUEST)

            serializer = FixedFileSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                serializer.save()
                return Response(status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk):
        fixing_file = get_object_or_404(FixedFile, id=pk)
        fixing_file.is_false_positive = not fixing_file.is_false_positive
        fixing_file.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        fixing_file = get_object_or_404(FixedFile, id=pk)
        fixing_file.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint to list and retrieve tasks.

    list:
    Retrieve all the tasks of a repository.

    retrieve:
    Retrieve a given task

    """
    def list(self, request, **kwargs):
        repository = self.request.query_params.get('repository', None)
        state = self.request.query_params.get('state', None)

        if not repository:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        repository = get_object_or_404(Repository, id=repository)

        if state:
            tasks = Task.objects.filter(repository=repository, state=state)
        else:
            tasks = Task.objects.filter(repository=repository)

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk):
        task = get_object_or_404(Task, id=pk)
        serializer = TaskSerializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ===================================================================================================================#

class GetPredictionView(APIView):
    """
    get:
    Get the prediction for an IaC script.
    """

    def get(self, request, pk):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class UpdatePredictionView(APIView):
    """
    put:
    Update a prediction obtained from the GET /predictions/ endpoint.
    """

    def put(self, request, pk):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


class ModelsViewSet(viewsets.ViewSet):
    """
    list:
    List all the pre-trained models.

    retrieve:
    Retrieve a pre-trained model.

    create:
    Upload a pre-trained model.

    destroy:
    Delete a pre-trained model.
    """

    def list(self, request):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def retrieve(self, request, pk=None):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def create(self, request, pk=None):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

    def destroy(self, request, pk=None):
        return Response(status=status.HTTP_501_NOT_IMPLEMENTED)
