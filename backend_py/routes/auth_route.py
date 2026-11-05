from fastapi import APIRouter

from controllers.auth_controller import LOGIN, signUpGenerateOTP, signUpVerifyOTP

router = APIRouter()

router.add_api_route("/signup-generate-otp", signUpGenerateOTP, methods=["POST"])
router.add_api_route("/signup-verify-otp", signUpVerifyOTP, methods=["POST"])
router.add_api_route("/login", LOGIN, methods=["POST"])
