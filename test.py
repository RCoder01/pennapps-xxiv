import asyncio
from viam.components.motor import Motor
from viam.robot.client import RobotClient
from viam.rpc.dial import Credentials, DialOptions
import cv2
import mediapipe as mp

class HandDetector():
    def __init__(self, mode = False, maxHands = 2, detectionCon = 0.5, trackCon = 0.5):
        self.mode = mode
        self.maxHands = maxHands
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands
        self.hands = self.mpHands.Hands()
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self,img, draw = True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)
        # print(self.results.multi_hand_landmarks)

        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo = 0, draw = True):
        lmlist = []
        if self.results.multi_hand_landmarks:
            if handNo >= len(self.results.multi_hand_landmarks):
                return []
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                lmlist.append([id, lm.x, lm.y, lm.z])
                if draw:
                    cv2.circle(img, (cx, cy), 3, (255, 0, 255), cv2.FILLED)
        return lmlist
    
def main():
    pTime = 0
    cTime = 0
    cap = cv2.VideoCapture(0)
    detector = HandDetector()

    while True:
        success, img = cap.read()
        img = detector.findHands(img)
        hand1 = detector.findPosition(img)
        hand2 = detector.findPosition(img, handNo=1)

        if hand1:
            tx, ty, tz = hand1[4][1:]
            px, py, pz = hand1[20][1:]
            # print(f'{x:.03}, \t{y:.03}, \t{z:.03}')
            print(f'hand1: {"left" if px < tx else "right"}, {"top" if ty < 0.5 else "bottom"}')
        if hand2:
            tx, ty, tz = hand2[4][1:]
            px, py, pz = hand2[20][1:]
            # print(f'{x:.03}, \t{y:.03}, \t{z:.03}')
            print(f'hand2: {"left" if px < tx else "right"}, {"top" if ty < 0.5 else "bottom"}')

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(img, str(int(fps)), (10, 70), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

        cv2.imshow("Image", img)
        cv2.waitKey(1)

async def connect():
    creds = Credentials(
        type='robot-location-secret',
        payload='3rn6lwpqwh5xzra3sy33x8ul94b5s20zf66ghe6v9bny577z')
    opts = RobotClient.Options(
        refresh_interval=0,
        dial_options=DialOptions(credentials=creds)
    )
    return await RobotClient.at_address('robot6-main.wkhwbmlw2g.viam.cloud', opts)

async def main():
    robot = await connect()

    print('Resources:')
    print(robot.resource_names)
    left = Motor.from_robot(robot=robot, name='left')
    right = Motor.from_robot(robot=robot, name='right')
    # await asyncio.gather(
    #     left.go_for(rpm=60, revolutions=1),
    #     right.go_for(rpm=60, revolutions=1)
    # )


    await robot.close()

if __name__ == '__main__':
    asyncio.run(main())