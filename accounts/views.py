from django.shortcuts import render
from rest_framework import generics
from .models import User
from .serializers import RegisterSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import UserSerializer
from .models import School, Role
from .serializers import SchoolSerializer
from .serializers import CreateUserByAdminSerializer
from .permissions import IsAdminUserRole, CanCreateSchool, IsSubscriptionActive
from rest_framework.generics import ListAPIView
from .models import User
from .serializers import UserSerializer
from .permissions import IsAdminUserRole
from rest_framework import status
from django.shortcuts import get_object_or_404
from .serializers import UpdateUserRoleSerializer
from .permissions import IsSubscriptionActive
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework import filters
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import AuditLog
from .serializers import AuditLogSerializer
from django.utils.dateparse import parse_date
from .models import StudentProfile
from .serializers import StudentProfileSerializer, SchoolSettingsSerializer
from .models import Assessment, StudentResult
from .serializers import AssessmentSerializer, StudentResultSerializer, FeePaymentSerializer
from django.http import FileResponse
from .report_pdf import generate_report_card_pdf
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .models import StudentProfile, StudentResult, Assessment
from django.db.models import Avg
from .models import FeePayment, StudentProfile, CBCEvidence
import json
from .cbc_ai_engine import CBCAIEngine
from .daraja_utils import DarajaClient
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from .models import FeeStructure

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

class ApiRootView(APIView):
    def get(self, request):
        return Response({
            "message": "Welcome to JODASA API",
            "endpoints": {
                "register": "/api/register/",
                "login": "/api/login/",
                "me": "/api/me/",
                "create_school": "/api/create-school/",
                "create_user": "/api/create-user/",
                "list_users": "/api/users/",
                "user_detail": "/api/users/<id>/",
                "update_role": "/api/users/<id>/role/",
                "delete_user": "/api/users/<id>/delete/",
                "list_students": "/api/students/",
                "student_detail": "/api/students/<id>/"
            }
        })

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id, school=request.user.school)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UpdateUserRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id, school=request.user.school)

        if user == request.user:
            return Response(
                {"error": "You cannot change your own role"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UpdateUserRoleSerializer(data=request.data)

        if serializer.is_valid():
            role_name = serializer.validated_data['role']
            role = Role.objects.get(name=role_name)

            user.role = role
            user.save()

            AuditLog.objects.create(
                school=request.user.school,
                user=request.user,
                action='update_role',
                target_email=user.email,
                ip_address=get_client_ip(request)
            ) 

            return Response({
                "message": "User role updated",
                "email": user.email,
                "new_role": role.name
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ListUsersView(ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'username']

    def get_queryset(self):
        queryset = User.objects.filter(school=self.request.user.school)
        
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role__name=role)

        return queryset
        

class CreateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def post(self, request):
        serializer = CreateUserByAdminSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            user = serializer.save()

           

            AuditLog.objects.create(
                school=request.user.school,
                user=request.user,
                action='create_user',
                target_email=user.email,
                ip_address=get_client_ip(request)
            )

            return Response({
                "message": "User created successfully",
                "email": user.email,
                "role": user.role.name
            })

        return Response(serializer.errors, status=400)

class CreateSchoolView(APIView):
    permission_classes = [CanCreateSchool]

    def post(self, request):
        serializer = SchoolSerializer(data=request.data)

        if serializer.is_valid():
            school = serializer.save()

            # assign current user to this school
            user = request.user
            user.school = school

            # assign admin role
            admin_role = Role.objects.get(name="admin")
            user.role = admin_role

            user.save()

            return Response({
                "message": "School created successfully",
                "school": serializer.data
            })

        return Response(serializer.errors, status=400)

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        school = request.user.school

        if school:
            school.update_subscription_status()

        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer


class DeleteUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id, school=request.user.school)

        # optional safety: prevent self-delete
        if user == request.user:
            return Response(
                {"error": "You cannot delete your own account"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = user.email

        AuditLog.objects.create(
                school=request.user.school,
                user=request.user,
                action='delete_user',
                target_email=email,                
                ip_address=get_client_ip(request)
            )

        user.delete()      

        return Response(
            {"message": "User deleted successfully"},
            status=status.HTTP_200_OK
        )

class ListStudentsView(ListAPIView):
    serializer_class = StudentProfileSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    filter_backends = [filters.SearchFilter]
    search_fields = ['user__email', 'admission_number', 'grade', 'stream']

    def get_queryset(self):
        return StudentProfile.objects.filter(
            user__school=self.request.user.school
        )

class StudentDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def get(self, request, student_id):
        student = get_object_or_404(
            StudentProfile,
            id=student_id,
            user__school=request.user.school
        )
        serializer = StudentProfileSerializer(student)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, student_id):
        student = get_object_or_404(
            StudentProfile,
            id=student_id,
            user__school=request.user.school
        )
        serializer = StudentProfileSerializer(student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AuditLogListView(ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    filter_backends = [filters.SearchFilter]
    search_fields = ['user__email', 'target_email', 'action']

    def get_queryset(self):
        queryset = AuditLog.objects.filter(
            user__school=self.request.user.school
        ).order_by('-timestamp')

        # 🔥 Filter by action
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)

        # 🔥 Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            queryset = queryset.filter(timestamp__date__gte=parse_date(start_date))

        if end_date:
            queryset = queryset.filter(timestamp__date__lte=parse_date(end_date))

        return queryset

class AssessmentListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole, IsSubscriptionActive]

    def get(self, request):
        assessments = Assessment.objects.filter(school=request.user.school)
        serializer = AssessmentSerializer(assessments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AssessmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(school=request.user.school)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StudentResultListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get(self, request):
        results = StudentResult.objects.filter(
            assessment__school=request.user.school
        )
        serializer = StudentResultSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = StudentResultSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(school=request.user.school)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StudentReportCardView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get(self, request, student_id):
        student = get_object_or_404(
            StudentProfile,
            id=student_id,
            user__school=request.user.school
        )

        term = request.query_params.get('term')
        
        results = StudentResult.objects.filter(
            student=student
        )
        
        if term:
            results = results.filter(assessment__term=term)

        subjects = []
        for result in results:
            percentage = (result.raw_score / result.assessment.max_marks) * 100
            subjects.append({
                'subject': result.assessment.subject,
                'term': result.assessment.term,
                'marks': f"{result.raw_score}/{result.assessment.max_marks}",
                'percentage': round(percentage, 2),
                'competency_level': result.competency_level,
                'teacher_remarks': result.teacher_remarks,
            })

        total_score = sum(r.raw_score for r in results)
        total_possible = sum(r.assessment.max_marks for r in results)
        average_percentage = round((total_score / total_possible) * 100, 2) if total_possible > 0 else 0

        competency_summary = {
            'EE': sum(1 for r in results if 'EE' in r.competency_level),
            'ME': sum(1 for r in results if 'ME' in r.competency_level),
            'AE': sum(1 for r in results if 'AE' in r.competency_level),
            'BE': sum(1 for r in results if 'BE' in r.competency_level),
        }

        return Response({
            'student': {
                'name': f"{student.user.first_name} {student.user.last_name}",
                'email': student.user.email,
                'admission_number': student.admission_number,
                'grade': student.grade,
                'stream': student.stream,
                'school': student.user.school.name,
            },
            'term': term or 'All Terms',
            'subjects': subjects,
            'summary': {
                'total_marks': f"{total_score}/{total_possible}",
                'average_percentage': average_percentage,
                'competency_summary': competency_summary,
            }
        }, status=status.HTTP_200_OK)

class StudentReportCardPDFView(APIView):
    permission_classes = [IsAuthenticated, IsSubscriptionActive]

    def get(self, request, student_id):
        student = get_object_or_404(
            StudentProfile,
            id=student_id,
            user__school=request.user.school
        )

        term = request.query_params.get('term')
        results = StudentResult.objects.filter(student=student)
        if term:
            results = results.filter(assessment__term=term)

        subjects = []
        for result in results:
            percentage = (result.raw_score / result.assessment.max_marks) * 100
            subjects.append({
                'subject': result.assessment.subject,
                'term': result.assessment.term,
                'marks': f"{result.raw_score}/{result.assessment.max_marks}",
                'percentage': round(percentage, 2),
                'competency_level': result.competency_level,
                'teacher_remarks': result.teacher_remarks,
            })

        total_score = sum(r.raw_score for r in results)
        total_possible = sum(r.assessment.max_marks for r in results)
        average_percentage = round((total_score / total_possible) * 100, 2) if total_possible > 0 else 0

        competency_summary = {
            'EE': sum(1 for r in results if 'EE' in r.competency_level),
            'ME': sum(1 for r in results if 'ME' in r.competency_level),
            'AE': sum(1 for r in results if 'AE' in r.competency_level),
            'BE': sum(1 for r in results if 'BE' in r.competency_level),
        }

        data = {
            'student': {
                'name': f"{student.user.first_name} {student.user.last_name}",
                'email': student.user.email,
                'admission_number': student.admission_number,
                'grade': student.grade,
                'stream': student.stream,
                'school': student.user.school.name,
            },
            'term': term or 'All Terms',
            'subjects': subjects,
            'summary': {
                'total_marks': f"{total_score}/{total_possible}",
                'average_percentage': average_percentage,
                'competency_summary': competency_summary,
            }
        }

        buffer = generate_report_card_pdf(data)

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=f"report_{student.admission_number}_{data['term']}.pdf"
        )

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])  # Safaricom hits this publicly without JWT
def mpesa_callback(request):
    stk_callback = request.data.get('Body', {}).get('stkCallback', {})
    result_code = stk_callback.get('ResultCode')
    checkout_request_id = stk_callback.get('CheckoutRequestID')

    try:
        # Find the pending payment record we created when triggering the STK push
        payment = FeePayment.objects.get(checkout_request_id=checkout_request_id)
        
        if result_code == 0:
            # Code 0 means Success
            metadata_items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt = None
            
            for item in metadata_items:
                if item.get('Name') == 'MpesaReceiptNumber':
                    mpesa_receipt = item.get('Value')
                    break
            
            # Update payment record to Completed
            payment.mpesa_receipt = mpesa_receipt
            payment.status = 'Completed'
            payment.description = f"Automated M-Pesa reconciliation. Receipt: {mpesa_receipt}"
            payment.save()
            print(f"✅ Payment reconciled successfully for Receipt: {mpesa_receipt}")
            
        else:
            # Any other code means user cancelled, insufficient funds, timeout, etc.
            payment.status = 'Failed'
            payment.description = f"Transaction failed. Safaricom ResultCode: {result_code}"
            payment.save()
            print(f"❌ Payment failed for CheckoutRequestID: {checkout_request_id}")

    except FeePayment.DoesNotExist:
        print(f"⚠️ Warning: Callback received for unknown CheckoutRequestID: {checkout_request_id}")
        
    # Safaricom expects a standard JSON acknowledgment response
    return Response({"ResultCode": 0, "ResultDesc": "Confirmation received successfully"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_class_ai_remarks(request):
    user = request.user
    school = user.school
    grade = request.data.get('grade')
    subject = request.data.get('subject')

    if not grade or not subject:
        return Response({"detail": "Please provide both grade and subject."}, status=400)

    # 1. Fetch all students belonging to this school in the specific grade
    students = StudentProfile.objects.filter(school=school, grade=grade)
    
    if not students.exists():
        return Response({"detail": "No students found in this grade."}, status=404)

    updated_count = 0

    # 2. Batch process every student using our AI Engine
    for student in students:
        # Fetch all results for this student in this specific subject, ordered by date
        results = StudentResult.objects.filter(
            school=school,
            student=student,
            assessment__subject=subject
        ).order_by('date_recorded') # Ensures oldest quiz is first, newest is last

        if results.exists():
            # Pass data to our engine
            smart_remark, prediction = CBCAIEngine.generate_remarks_and_predictions(
                student_profile=student,
                subject=subject,
                current_results=results
            )
            
            # Update the latest result record with the AI-generated insight
            latest_result = results.last()
            latest_result.teacher_remarks = smart_remark
            # Optional: You could save the prediction string into a dedicated status field if you decide to track it
            latest_result.save()
            updated_count += 1

    return Response({
        "message": f"Successfully processed {updated_count} student profiles.",
        "status": "Success"
    }, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    user = request.user
    school = user.school
    
    # Simple validation check to ensure a tenant school is bound to the user
    if not school:
        return Response({"detail": "User account is not linked to any registered school."}, status=400)
        
    amount = request.data.get('amount')
    phone = request.data.get('phone')
    student_id = request.data.get('student_id')
    
    if not amount or not phone or not student_id:
        return Response({"detail": "Missing dynamic fields: amount, phone, or student_id required."}, status=400)
    
    # 1. Initialize Daraja with the current school's specific credentials
    client = DarajaClient(
        consumer_key=school.mpesa_consumer_key,
        consumer_secret=school.mpesa_consumer_secret,
        shortcode=school.mpesa_shortcode
    )
    
    # 2. Trigger STK Push
    # Replace this placeholder string with your live deployed production domain later on Railway
    callback_url = "https://jodasa-backend-production.up.railway.app/api/payments/callback/"
    response = client.trigger_stk_push(phone, amount, callback_url)
    
    if response.get('ResponseCode') == '0':
        # 3. Securely create a record marked as Pending
        FeePayment.objects.create(
            school=school,
            student_id=student_id,
            amount_paid=amount,
            checkout_request_id=response.get('CheckoutRequestID'),
            status='Pending'
        )
        return Response({"message": "STK Push Sent Successfully", "status": "Pending"}, status=200)
    
    return Response({"error": "Safaricom Daraja API rejected the process request.", "detail": response}, status=400)    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_cbc_evidence(request):
    user = request.user
    school = user.school
        
    student_id = request.data.get('student_id')
    subject = request.data.get('subject')
    competency = request.data.get('competency')
    image_file = request.FILES.get('image')
    notes = request.data.get('notes', '')

    if not student_id or not image_file or not competency:
        return Response({"detail": "Missing student ID, image, or competency tag."}, status=400)

    try:
        student = StudentProfile.objects.get(id=student_id, school=school)
        
        evidence = CBCEvidence.objects.create(
            school=school,
            student=student,
            subject=subject,
            competency_tagged=competency,
            evidence_image=image_file,
            teacher_notes=notes
        )
        
        return Response({
            "message": "✅ Evidence uploaded and linked to KNEC compliance tracker successfully!",
            "id": evidence.id
        }, status=201)

    except StudentProfile.DoesNotExist:
        return Response({"detail": "Student record not found."}, status=404)

class SchoolSettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request):
        school = request.user.school
        if not school:
            return Response({"error": "No school linked."}, status=400)
        serializer = SchoolSettingsSerializer(school, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Settings updated."})
        return Response(serializer.errors, status=400)

class FeePaymentListView(ListAPIView):
    serializer_class = FeePaymentSerializer
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get_queryset(self):
        return FeePayment.objects.filter(school=self.request.user.school).order_by('-timestamp')

# views.py
class FeeStructureListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUserRole]

    def get(self, request):
        structures = FeeStructure.objects.filter(school=request.user.school)
        # inline serialize
        data = [{'grade': f.grade, 'term': f.term, 'total_amount': str(f.total_amount)} for f in structures]
        return Response(data)

    def post(self, request):
        grade = request.data.get('grade')
        term = request.data.get('term')
        amount = request.data.get('total_amount')
        FeeStructure.objects.update_or_create(
            school=request.user.school, grade=grade, term=term,
            defaults={'total_amount': amount, 'year': 2026}
        )
        return Response({"message": "Fee structure saved."}, status=201)
# Create your views here.